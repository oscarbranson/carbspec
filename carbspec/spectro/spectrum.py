import os
import numpy as np
import pandas as pd
import uncertainties as un
import uncertainties.unumpy as unp
import matplotlib.pyplot as plt
import pickle

from carbspec.spectro.mixture import unmix_spectra, pH_from_F, make_mix_spectra, make_mix_components
from carbspec.alkalinity import TA_from_pH
from carbspec.dye import K_handler

class Spectrum:
    def __init__(self, 
                 sample, timestamp, temp, sal, dye, splines, config_file, 
                 wv, dark=None, scale_factor=None, light_sample_raw=None, light_reference_raw=None):
        
        # metadata
        self.config_file = config_file
        self.timestamp = timestamp
        self.sample = sample
        self.dye = dye
        self.splines = splines
        self.temp = temp
        self.sal = sal

        # data
        self.wv = wv
        self.dark = dark
        self.scale_factor = scale_factor
        self.light_sample_raw = light_sample_raw
        self.light_reference_raw = light_reference_raw
        
        # calculated
        self.light_reference = None
        self.light_sample = None

        if self.scale_factor is not None:
            self.correct_channels()

        if self.light_sample is not None and self.light_reference is not None:
            self.calc_absorbance()
    
    def correct_channels(self):
        self.light_reference = self.light_reference_raw - self.dark
        self.light_sample = self.light_sample_raw / self.scale_factor - self.dark
    
    def calc_absorbance(self):
        self.absorbance = -1 * np.log10(self.light_sample / self.light_reference)
            
    # io functions
    def to_pickle(self, file):
        with open(file, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
    
    @staticmethod
    def from_pickle(file):
        with open(file, 'rb') as f:
            return pickle.load(f)

    def to_dat(self, file):
        vardict = {
            'wv': self.wv,
            'dark': self.dark,
            'light_reference_raw': self.light_reference_raw,
            'light_sample_raw': self.light_sample_raw,
            'scale_factor': self.scale_factor,
            'absorbance': self.absorbance,
        }
        
        vars = [k for k in vardict if vardict[k] is not None]
        out = np.vstack([vardict[k] for k in vars]).T

        header = [
            f'# timestamp: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}',
            f'# sample: {self.sample}',
            f'# temp: {self.temp:.3f}',
            f'# sal: {self.sal:.2f}',
            f'# config_file: {self.config_file}',
            f'# dye: {self.dye}',
            f'# splines: {self.splines}'
        ]
        
        header = '\n'.join(header + [','.join(vars)])

        np.savetxt(file, out, delimiter=',', header=header, comments='')
    
    @staticmethod
    def from_csv(file):
        # read header
        with open(file, 'r') as f:
            timestamp = f.readline()
            sample = f.readline()
            temp = f.readline()
            sal = f.readline()
            config_file = f.readline()
            dye = f.readline()
            splines = f.readline()
        
        # parse header
        timestamp = pd.to_datetime(timestamp.split(': ')[-1].strip())
        sample = sample.split(': ')[-1].strip()
        temp = float(temp.split(': ')[-1].strip())
        sal = float(sal.split(': ')[-1].strip())
        config_file = config_file.split(': ')[-1].strip()
        dye = dye.split(': ')[-1].strip()
        splines = splines.split(': ')[-1].strip()
        
        # read data
        dat = pd.read_csv(file, comment='#')
        
        if 'light_reference_raw' in dat.columns:
            light_reference_raw = dat.light_reference_raw
        else:
            light_reference_raw = None
        
        if 'light_sample_raw' in dat.columns:
            light_sample_raw = dat.light_sample_raw
        
        
        return Spectrum(timestamp=timestamp, sample=sample, wv=dat['wv'], config_file=config_file, dark=dat['dark'], scale_factor=dat['scale_factor'], light_sample_raw=light_sample_raw, light_reference_raw=light_reference_raw, temp=temp, sal=sal, dye=dye, splines=splines)
    
    def save(self, dat_file, pkl_file):
        self.to_dat(dat_file)
        self.to_pickle(pkl_file)
    
    @staticmethod
    def load(file):
        if 'pkl' in file:
            return Spectrum.from_pickle(file)
        elif 'csv' in file:
            return Spectrum.from_csv(file)
        else:
            raise ValueError('File must be a .csv or .pkl file.')
    
    def __repr__(self):
        return f'Spectrum from sample {self.sample} at {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}'
    
def calc_pH(spectrum):
    """Calculate pH from a spectrum

    Returns
    -------
    tuple
        F, K, pH, fit_p
    """
    fit_p = un.correlated_values(*unmix_spectra(spectrum.wv, spectrum.absorbance, spectrum.splines))
    F = fit_p[1] / fit_p[0]
    K = K_handler(spectrum.splines, spectrum.temp, spectrum.sal)
    pH = pH_from_F(F, K)
    
    return F, K, pH, fit_p
