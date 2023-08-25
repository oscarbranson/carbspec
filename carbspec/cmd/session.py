import datetime as dt
import os
import numpy as np
import pandas as pd
from configparser import ConfigParser
import pkg_resources as pkgrs
import time
import pyperclip
import matplotlib.pyplot as plt
import uncertainties as un
import uncertainties.unumpy as unp

try:
    from carbspec.instruments import BeamSwitch, Spectrometer, TempProbe
    dummy = False
except:
    print('Instrument connection error: using dummy instruments')
    from carbspec.instruments.dummy import BeamSwitch, Spectrometer, TempProbe
    dummy = True

from carbspec.spectro.spectrum import Spectrum
from carbspec.alkalinity import calc_acid_strength

class pHMeasurementSession:
    def __init__(self, dye='MCP', config_file=None, save=True, plotting=True):

        self.dye = dye
        
        if config_file is None:
            config_file = pkgrs.resource_filename('carbspec', '/cmd/resources/carbspec.cfg')
        self.config_file = config_file
        self.readConfig()
        
        self.plotting = plotting
        
        # set up variables
        self.timestamp = dt.datetime.now().replace(microsecond=0)
        self.sample = None
        self.sal = self.config.getfloat('salinity')
        self.temp = None
        self.wv = None
        self.dark = None
        self.light_reference_raw = None
        self.light_sample_raw = None
        self.scale_factor = None
        
        self.boxcar_width = self.config.getint('spec_boxcarwidth')
        self.splines = self.config.get('splines')

        self.connect_Instruments()
        
        self.savedir = self.config['savedir']
        os.makedirs(self.savedir, exist_ok=True)
        
        # Spectra Saving
        self.save = save
        if self.save:
            print(f'Saving data to {self.savedir}')
        
        # Summary File Saving
        self.summary_dat = os.path.join(self.savedir, f"{self.dye}_summary.dat")
        self.summary_pkl = os.path.join(self.savedir, f"{self.dye}_summary.pkl")
        
        if os.path.exists(self.summary_pkl):
            self.data_table = pd.read_pickle(self.summary_pkl)
        else:
            self.data_table = pd.DataFrame(index=None, columns=['sample', 'temp', 'sal', 'F', 'K', 'pH', 'spectra'])
            self.data_table.index.name = 'timestamp'

        print('  --> Ready!')

    def readConfig(self):
        self._config = ConfigParser()
        self._config.read(self.config_file)
        self.config = self._config[self.dye]
        
    def writeConfig(self):
        with open(self.config_file, 'w') as f:
            self._config.write(f)
    
    def updateConfig(self, parameter, value, section=None):
        if section is None:
            section = self.dye
        if parameter in self._config['DEFAULT']:
            self._config.set(section, parameter, str(value))
            
    def connect_TempProbe(self):
        self.temp_probe = TempProbe(
            averaging_period=self.config.getint('temp_integrationtime'),
            m=self.config.getfloat('temp_m'), 
            c=self.config.getfloat('temp_c')
            )
        
    def connect_BeamSwitch(self):
        self.beam_switch = BeamSwitch(
            reverse_sides=self.config.getboolean('beamswitch_reversechannels')
            )
    
    def connect_Spectrometer(self):
        self.spectrometer = Spectrometer()
        
        self.spectrometer.set_integration_time_ms(self.config.getint('spec_integrationtime'))
                
        self._wv = self.spectrometer.wv
        self._wv_filter = (self._wv >= self.config.getfloat('spec_wvmin')) & (self._wv <= self.config.getfloat('spec_wvmax'))

        self.wv = self._wv[self._wv_filter]
    
    def connect_Instruments(self):
        self.connect_TempProbe()
        self.connect_BeamSwitch()
        self.connect_Spectrometer()
            
    def find_max_integration_time(self, maintain_total_collection_time=True):
        
        total_collection_time = self.config.getint('spec_nscans') * self.config.getint('spec_integrationtime')
        
        ref_integration_time = 1
        sample_integration_time = 1

        self.beam_switch.reference_cell()
        time.sleep(0.1)
        
        self.spectrometer.set_integration_time_ms(ref_integration_time)
        trans = self.spectrometer.read()[self._wv_filter]

        while trans.max() < 5.5e4:
            ref_integration_time += 1
            self.spectrometer.set_integration_time_ms(ref_integration_time)
            trans = self.spectrometer.read()[self._wv_filter]

        self.beam_switch.sample_cell()
        time.sleep(0.1)

        self.spectrometer.set_integration_time_ms(sample_integration_time)
        trans = self.spectrometer.read()[self._wv_filter]

        while trans.max() < 5.5e4:
            sample_integration_time += 1
            self.spectrometer.set_integration_time_ms(sample_integration_time)
            trans = self.spectrometer.read()[self._wv_filter]

        max_integration_time = min(ref_integration_time, sample_integration_time)
        
        self.spectrometer.set_integration_time_ms(max_integration_time)
        
        new_total_collection_time = max_integration_time * self.config.getint('spec_nscans')
        
        if new_total_collection_time < total_collection_time and maintain_total_collection_time:
            self.updateConfig('spec_nscans', int(total_collection_time / max_integration_time), section='DEFAULT')
        
        self.updateConfig('spec_integrationtime', max_integration_time, section='DEFAULT')
        
        self.writeConfig()
        
    def read_spectrometer(self):
        spec = np.zeros_like(self._wv)
        for i in range(self.config.getint('spec_nscans')):
            spec += self.spectrometer.read()
        spec /= self.config.getint('spec_nscans')
        
        if self.boxcar_width is not None:
            spec = np.convolve(spec, np.ones(self.boxcar_width) / self.boxcar_width, mode='same')

        return spec[self._wv_filter]

    def collect_dark(self):
        input('Ensure the light is off and the reference cell is in the beam path. Press enter to continue.')
        self.dark = self.read_spectrometer()
        self.spectrum = Spectrum(self)
        if self.plotting:
            self.spectrum.plot('raw')
    
    def collect_scale_factor(self):
        input('Place the reference material in both cells. Switch the light source on. Press enter to continue.')
        self.scale_factor = np.ones_like(self.wv)
        self.collect_spectrum('setup')
        self.scale_factor = self.light_sample_raw / self.light_reference_raw
        self.spectrum.save(vars=['wv','dark','light_reference', 'light_sample','scale_factor'])
        
        self.light_sample = self.light_sample_raw / self.scale_factor - self.dark
        
        if self.plotting:
            self.spectrum.plot(['raw', 'scale factor', 'dark corrected'])
    
    def collect_spectrum(self, sample_name=None):
        self.sample = sample_name
        
        temp_start = self.temp_probe.read()
        
        self.beam_switch.reference_cell()
        if dummy:
            self.spectrometer.reference_cell()  # for dummy
        time.sleep(0.1)
        self.light_reference_raw = self.read_spectrometer()
        
        temp_mid = self.temp_probe.read()
        time.sleep(0.1)
        
        self.beam_switch.sample_cell()
        if dummy:
            self.spectrometer.sample_cell()  # for dummy
        time.sleep(0.1)
        
        self.light_sample_raw = self.read_spectrometer()
        
        temp_end = self.temp_probe.read()
        
        self.temp = (temp_start + temp_mid + temp_end) / 3.
        
        self.timestamp = dt.datetime.now().replace(microsecond=0)

        self.spectrum = Spectrum(self)
                
        self.data_table.loc[self.timestamp, ['sample', 'sal', 'temp', 'spectra']] = self.sample, self.sal, self.temp, self.spectrum
    
    def measure_sample(self, sample_name=None, salinity=None, plot_vars=['absorbance', 'residuals', 'dark corrected']):
        if self.dark is None:
            raise ValueError('Dark spectrum not collected. Run collect_dark() first.')
        if self.scale_factor is None:
            raise ValueError('Scale factor not calculated. Run collect_scale_factor() first.')

        if salinity is not None:
            self.sal = salinity
            
        self.collect_spectrum(sample_name=sample_name)
        self.spectrum.calc_absorbance()
        
        self.spectrum.calc_pH()
        
        self.data_table.loc[self.timestamp, ['F', 'K', 'pH']] = self.spectrum.F, self.spectrum.K, self.spectrum.pH

        self.spectrum.save()
        self.save_summary()
                
        if self.plotting:
            self.spectrum.plot(include=plot_vars)
            
    def save_summary(self):
        if not os.path.exists(self.summary_dat):
            header = 'datetime,sample,dye,sal,temp,K,F,pH\n'
            with open(self.summary_dat, 'w+') as f:
                f.write(header)

        data = f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')},{self.sample},{self.dye},{self.sal:.2f}, {self.temp:.2f},{self.spectrum.K:.4e},{self.spectrum.F:.4e},{self.spectrum.pH:.4f}\n"
        
        with open(self.summary_dat, 'a') as f:
            f.write(data)
        
        self.data_table.to_pickle(self.summary_pkl)
                
class TAMeasurementSession(pHMeasurementSession):
    def __init__(self, dye='BPB', config_file=None, save=True, plotting=True):
        super().__init__(dye=dye, config_file=config_file, save=save, plotting=plotting)
        
        self.sample_weight_spreadsheet = self.config.get('sample_weight_spreadsheet')
        
        self.data_table = pd.DataFrame(index=None, columns=['sample', 'temp', 'sal', 'F', 'K', 'pH', 'm_sample', 'm_acid', 'C_acid', 'TA', 'spectra'])
        self.data_table.index.name = 'timestamp'
    
    def get_sample_weights(self, crm=False, all=False):
        valid_input = False
        while not valid_input:
            all_weights = pd.read_excel(self.sample_weight_spreadsheet, parse_dates=['timestamp'])
            all_weights.set_index('timestamp', inplace=True)
            
            weights = all_weights.loc[self.timestamp, :]
            
            if weights.empty:
                input(f'Sample {self.sample} at {self.timestamp} is not in the weight spreadsheet.\n Check the spreadsheet, resave it, then press Enter to continue.')
                continue
            
            if np.isnan(weights['+sample']):
                input('No sample weight present. Please check the spreadsheet, resave it, then press Enter to continue.')
                continue
            
            if np.isnan(weights['+acid']):
                input('No acid weight present. Please check the spreadsheet, resave it, then press Enter to continue.')
                continue
            
            if not crm:
                if np.isnan(weights['C_acid']):
                    input('No acid concentration present. Please check the spreadsheet, resave it, then press Enter to continue.')
                    continue

            valid_input = True
            
            if all:
                return all_weights
            
            return weights

    def save_summary(self):
        if not os.path.exists(self.summary_dat):
            header = 'datetime,sample,dye,sal,temp,K,F,pH,m_sample,m_acid,C_acid,TA\n'
            with open(self.summary_dat, 'w+') as f:
                f.write(header)

        data = f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')},{self.sample},{self.dye},{self.sal:.2f}, {self.temp:.2f},{self.spectrum.K:.4e},{self.spectrum.F:.4e},{self.spectrum.pH:.4f},{self.spectrum.m_sample:.5f},{self.spectrum.m_acid:.5f},{self.spectrum.C_acid:.12f},{self.spectrum.TA:.2f}\n"
        
        with open(self.summary_dat, 'a') as f:
            f.write(data)
            
        self.data_table.to_pickle(self.summary_pkl)
    
    def measure_CRM(self, crm_alk, salinity, plot_vars=['absorbance', 'residuals', 'dark corrected']):
        
        sample_name = 'CRM'
        self.TA = crm_alk
        
        initial_salinity = self.sal
        self.sal = salinity
        
        if self.dark is None:
            raise ValueError('Dark spectrum not collected. Run collect_dark() first.')
        if self.scale_factor is None:
            raise ValueError('Scale factor not calculated. Run collect_scale_factor() first.')
        
        if salinity is not None:
            self.sal = salinity
        
        self.collect_spectrum(sample_name=sample_name)
        
        self.spectrum.calc_absorbance()
        self.spectrum.calc_pH()

        self.data_table.loc[self.timestamp, ['F', 'K', 'pH']] = [self.spectrum.F, self.spectrum.K, self.spectrum.pH]

        sample_info = f'{self.timestamp}'
        pyperclip.copy(sample_info)
        print(sample_info)
        
        input('Copy the timestamp into the spreadsheet (from the clipboard), save the spreadsheet, then press Enter to continue.')
        
        weights = self.get_sample_weights(crm=True)
        
        self.spectrum.TA = crm_alk
        self.spectrum.m_sample = weights['m_sample']
        self.spectrum.m_acid = weights['m_acid']
        
        self.spectrum.C_acid = calc_acid_strength(crm_alk=crm_alk, pH=self.spectrum.pH, m0=self.spectrum.m_sample, m=self.spectrum.m_acid, sal=self.spectrum.sal, temp=self.spectrum.temp)
        
        self.data_table.loc[self.timestamp, ['m_sample', 'm_acid', 'C_acid', 'TA']] = [self.spectrum.m_sample, self.spectrum.m_acid, self.spectrum.C_acid, self.spectrum.TA]
        
        print(f'Calibrated acid strength: {self.C_acid} (copied to clipboard)')
        acid_strength = f'{self.C_acid}'
        pyperclip.copy(acid_strength)
        
        self.spectrum.save()
        self.save_summary()
                
        if self.plotting:
            self.spectrum.plot(include=plot_vars)
            
        self.sal = initial_salinity
            
    def measure_sample(self, sample_name=None, salinity=None, plot_vars=['absorbance', 'residuals', 'dark corrected']):
        
        if self.dark is None:
            raise ValueError('Dark spectrum not collected. Run collect_dark() first.')
        if self.scale_factor is None:
            raise ValueError('Scale factor not calculated. Run collect_scale_factor() first.')
        
        if salinity is not None:
            self.sal = salinity
        
        self.collect_spectrum(sample_name=sample_name)
        self.spectrum.calc_absorbance()
        
        self.spectrum.calc_pH()
        self.data_table.loc[self.timestamp, ['F', 'K', 'pH']] = [self.spectrum.F, self.spectrum.K, self.spectrum.pH]

        sample_info = f'{self.timestamp}'
        pyperclip.copy(sample_info)
        print(sample_info)
        
        input('Copy the timestamp into the spreadsheet (from the clipboard), save the spreadsheet, then press Enter to continue.')

        weights = self.get_sample_weights()
        self.spectrum.calc_TA(m_sample=weights['m_sample'], m_acid=weights['m_acid'], C_acid=weights['C_acid'])
        
        self.data_table.loc[self.timestamp, ['m_sample', 'm_acid', 'C_acid', 'TA']] = [self.spectrum.m_sample, self.spectrum.m_acid, self.spectrum.C_acid, self.spectrum.TA]
        
        self.spectrum.save()
        self.save_summary()
                
        if self.plotting:
            self.spectrum.plot(include=plot_vars)