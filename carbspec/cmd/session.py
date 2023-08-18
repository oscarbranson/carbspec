import datetime as dt
import os
import numpy as np
from configparser import ConfigParser
import pkg_resources as pkgrs
import time
import matplotlib.pyplot as plt
import uncertainties as un
import uncertainties.unumpy as unp

from carbspec.instruments.dummy import BeamSwitch, Spectrometer, TempProbe
# from carbspec.instruments import BeamSwitch, Spectrometer, TempProbe

from carbspec.dye import K_handler
from carbspec.spectro.mixture import unmix_spectra, pH_from_F, make_mix_spectra
from carbspec.dye.splines import load_splines

class MeasurementSession:
    def __init__(self, dye='MCP', config_file=None, save=True, plotting=True):

        self.dye = dye
        
        if config_file is None:
            config_file = pkgrs.resource_filename('carbspec', '/cmd/resources/carbspec.cfg')
        self.config_file = config_file
        self.readConfig()
        
        self.plotting = plotting
        
        # set up variables
        self.timestamp = None
        self.sample = None
        self.sal = self.config.getfloat('salinity')
        self.temp = None
        self.wv = None
        self.dark = None
        self.scale_factor = None
        self.light_reference = None
        self.light_sample = None
        self.absorbance = None
        
        self.fit_p = None
        self.F = None
        self.K = None
        self.pH = None
        
        self._spec_fn = make_mix_spectra(self.dye)
        self._splines = load_splines(self.dye)
        
        self.connect_Instruments()
        
        self.savedir = self.config['savedir']
        os.makedirs(self.savedir, exist_ok=True)
        
        # Spectra Saving
        self.save = save
        if self.save:
            print(f'Saving spectra to {self.savedir}')
        
        # Summary File Saving
        self.summary_file = os.path.join(self.savedir, f"{self.dye}_summary.csv")
        if self.summary_file is not None:
            print(f'Saving summary to {self.summary_file}')

        print('  --> Ready!')

    def readConfig(self):
        self._config = ConfigParser()
        self._config.read(self.config_file)
        self.config = self._config[self.dye]
        
    def writeConfig(self):
        with open(self.config_file, 'w') as f:
            self._config.write(f)
    
    def updateConfig(self, parameter, value):
        if parameter in self._config['DEFAULT']:
            self._config.set('LAST', parameter, str(value))
            
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
        # if self.config['spec_id'] == '':
        #     spec_id = 
        self.spectrometer = Spectrometer()
        
        self.spectrometer.set_integration_time_ms(self.config.getint('spec_integrationtime'))
        self.spectrometer.set_wavelength_range(self.config.getfloat('spec_wvmin'), self.config.getfloat('spec_wvmax'))
        self.boxcar_width = self.config.getint('spec_boxcarwidth')
        
        self.wv = self.spectrometer.wv
    
    def connect_Instruments(self):
        self.connect_TempProbe()
        self.connect_BeamSwitch()
        self.connect_Spectrometer()
            
    def read_spectrometer(self):
        spec = np.zeros_like(self.wv)
        for i in range(self.config.getint('spec_nscans')):
            spec += self.spectrometer.read()
        return spec

    def collect_dark(self):
        input('Ensure the light is off and the reference cell is in the beam path. Press enter to continue.')
        self.dark = self.read_spectrometer()
        if self.plotting:
            self.plot_spectrum('raw')
    
    def collect_scale_factor(self):
        input('Place the reference material in both cells. Switch the light source on. Press enter to continue.')
        self.scale_factor = np.ones_like(self.wv)
        self.collect_spectrum()
        self.scale_factor = self.light_sample / self.light_reference
        self.save_spectrum(vars=['wv','dark','light_reference', 'light_sample','scale_factor'])
        
        self.light_sample /= self.scale_factor
        
        if self.plotting:
            self.plot_spectrum(['raw', 'scale factor', 'dark corrected'])
    
    def collect_spectrum(self, sample_name=None):
        self.sample = sample_name
        
        temp_start = self.temp_probe.read()
        
        self.beam_switch.reference_cell()
        self.spectrometer.reference_cell()  # for dummy
        time.sleep(0.1)
        self.light_reference = self.read_spectrometer()
        
        temp_mid = self.temp_probe.read()
        time.sleep(0.1)
        
        self.beam_switch.sample_cell()
        self.spectrometer.sample_cell()  # for dummy
        time.sleep(0.1)
        self.light_sample = self.read_spectrometer() / self.scale_factor
        
        temp_end = self.temp_probe.read()
        
        self.temp = (temp_start + temp_mid + temp_end) / 3
        
        self.timestamp = dt.datetime.now()
                
    def calc_absorbance(self):
        self.absorbance = np.log10(self.light_reference / self.light_sample)
    
    def calc_pH(self):
        self.fit_p = un.correlated_values(*unmix_spectra(self.wv, self.absorbance, 'MCP'))
        self.F = self.fit_p[1] / self.fit_p[0]
        self.K = K_handler(self.dye, self.temp, self.sal)
        self.pH = pH_from_F(self.F, self.K)
    
    def measure_sample(self, sample_name=None, plot_vars=['absorbance', 'dark corrected', 'scale factor', 'raw', ]):
        if self.dark is None:
            raise ValueError('Dark spectrum not collected. Run collect_dark() first.')
        if self.scale_factor is None:
            raise ValueError('Scale factor not calculated. Run collect_scale_factor() first.')
        
        self.collect_spectrum(sample_name=sample_name)
        self.calc_absorbance()
        
        self.calc_pH()

        self.save_spectrum()
        self.save_summary()
                
        if self.plotting:
            self.plot_spectrum(include=plot_vars)
    
    def save_spectrum(self, filename=None, vars=['wv','dark','light_reference','light_sample','scale_factor','absorbance']):
    
        if filename is None:
            filename = f"{self.dye}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
        if self.sample is not None:
            filename = filename.replace('.csv', f'_{self.sample}.csv')
        
        outfile = os.path.join(self.savedir, filename)
        
        vardict = {
            'wv': self.wv,
            'dark': self.dark,
            'light_reference': self.light_reference,
            'light_sample': self.light_sample,
            'scale_factor': self.scale_factor,
            'absorbance': self.absorbance,
        }
        
        out = np.vstack([vardict[k] for k in vars]).T

        header = '\n'.join([
            f'# Config: {self.config_file}',
            f'# Time: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}',
            f'# Temp: {self.temp:.2f}',
            f'# Sal: {self.sal:.2f}',
            ','.join(vars)
            ])

        np.savetxt(outfile, out, delimiter=',', header=header, comments='')
    
    def save_summary(self):
        if not os.path.exists(self.summary_file):
            header = 'datetime,sample,dye,sal,temp,K,F,pH\n'
            with open(self.summary_file, 'w+') as f:
                f.write(header)

        data = f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')},{self.sample},{self.dye},{self.sal:.2f}, {self.temp:.2f},{self.K:.4e},{self.F:.4e},{self.pH:.4f}\n"
        
        with open(self.summary_file, 'a') as f:
            f.write(data)
    
    def calc_fit_components(self):
        p = unp.nominal_values(self.fit_p)

        pred = self._spec_fn(self.wv, *p)

        x = self.wv
        baseline = baseline = np.full(x.size, p[2])
        xm = p[-2] + x * p[-1]
        acid = baseline + self._splines['acid'](xm) * p[0]
        base = baseline + self._splines['base'](xm) * p[1]
        
        return pred, acid, base
    
    def plot_spectrum(self, include=['absorbance', 'dark corrected', 'scale factor', 'raw', ]):
        if isinstance(include, str):
            include = [include]
        
        heights = {
            'raw': 1,
            'scale factor': 0.5,
            'dark corrected': 1, 
            'absorbance': 1,
        }
        
        height_ratios = [heights[k] for k in include]
        
        fig, axs = plt.subplots(len(include), 1, figsize=(5, 0.5 + 1.5 * len(include)), constrained_layout=True, sharex=True, height_ratios=height_ratios)

        if len(include) == 1:
            axs = [axs]
            
        for i, var in enumerate(include):
            match var:
                case 'raw':
                    axs[i].plot(self.wv, self.dark, label='dark', color='grey')
                    if self.light_reference is not None:
                        axs[i].plot(self.wv, self.light_reference, label='reference', color='C0')
                    if self.light_sample is not None:
                        axs[i].plot(self.wv, self.light_sample * self.scale_factor, label='sample', color='C1')
                    axs[i].set_ylabel('raw counts')
                case 'scale factor':
                    axs[i].plot(self.wv, self.scale_factor, label='scale factor', color='C3')
                case 'dark corrected':
                    axs[i].plot(self.wv, self.light_reference - self.dark, label='reference', color='C0')
                    axs[i].plot(self.wv, self.light_sample - self.dark, label='sample', color='C1')
                    axs[i].set_ylabel('counts - dark')
                case 'absorbance':
                    axs[i].scatter(self.wv, self.absorbance, label='sample', color='k', s=1)
                    
                    if self.fit_p is not None:
                        pred, acid, base = self.calc_fit_components()
                        axs[i].plot(self.wv, pred, color='r', lw=1, label='fit')
                        axs[i].fill_between(self.wv, 0, acid, alpha=0.2, label='acid')
                        axs[i].fill_between(self.wv, 0, base, alpha=0.2, label='base')
                    
                    axs[i].set_ylabel('absorbance')

        axs[-1].set_xlim(self.config.getfloat('spec_wvmin'), self.config.getfloat('spec_wvmax'))
        axs[-1].set_xlabel('wavelength (nm)')

        title = ''
        if self.sample is not None:
            title += self.sample
        
        if self.pH is not None:
            title += f" : {self.pH:.4f}"
            
        axs[0].set_title(title, fontsize=8, loc='left')

        for ax in axs:
            ax.legend(fontsize=8, bbox_to_anchor=(1, 1), loc='upper left')
            
        return fig, axs