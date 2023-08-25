import os
import numpy as np
import uncertainties as un
import uncertainties.unumpy as unp
import matplotlib.pyplot as plt
import pickle

from carbspec.spectro.mixture import unmix_spectra, pH_from_F, make_mix_spectra, make_mix_components
from carbspec.alkalinity import TA_from_pH
from carbspec.dye import K_handler

class Spectrum:
    def __init__(self, session):
        self.temp = session.temp
        self.sal = session.sal
        self.timestamp = session.timestamp
        self.sample = session.sample
        self.savedir = session.savedir
        self.config_file = session.config_file
        
        self.dye = session.dye
        self.splines = session.splines
        
        self.wv = session.wv
        self.dark = session.dark
        self.light_reference_raw = session.light_reference_raw
        self.light_sample_raw = session.light_sample_raw
        self.scale_factor = session.scale_factor
        
        self.light_reference = None
        if self.light_reference_raw is not None:
            self.light_reference = self.light_reference_raw - self.dark
        self.light_sample = None
        if self.light_sample_raw is not None:
            self.light_sample = self.light_sample_raw / self.scale_factor - self.dark
        
        self.config = session.config
        
        self.absorbance = None
        self.fit_p = None
        self.F = None
        self.K = None
        self.pH = None
        
    # def __init__(self, wv, dark, light_reference_raw, light_sample_raw, scale_factor, temp, sal, timestamp, dye, splines, sample, savedir, config):
        
    #     self.temp = temp
    #     self.sal = sal
    #     self.timestamp = timestamp
    #     self.sample = sample
    #     self.savedir = savedir
        
    #     self.dye = dye
    #     self.splines = splines
        
    #     self.wv = wv
    #     self.dark = dark
    #     self.light_reference_raw = light_reference_raw
    #     self.light_sample_raw = light_sample_raw
    #     self.scale_factor = scale_factor
        
    #     self.light_reference = self.light_reference_raw - self.dark
    #     self.light_sample = self.light_sample_raw / self.scale_factor - self.dark
        
    #     self.config = config
        
    #     self.fit_p = None
    #     self.F = None
    #     self.K = None
    #     self.pH = None
        
        self._rawdir = os.path.join(self.savedir, 'raw')
        os.makedirs(self._rawdir, exist_ok=True)
        self._pkldir = os.path.join(self.savedir, 'pkl')
        os.makedirs(self._pkldir, exist_ok=True)
        self.summary_file = os.path.join(self.savedir, f"{self.dye}_summary.dat")        

        self.filename = f"{self.dye}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}"
        if self.sample is not None:
            self.filename = self.filename + f'_{self.sample}'
        self._pkl_outfile = os.path.join(self.savedir, 'pkl', self.filename + '.pkl')
        self._raw_outfile = os.path.join(self.savedir, 'raw', self.filename + '.csv')

        
    def calc_absorbance(self):
        self.absorbance = -1 * np.log10(self.light_sample / self.light_reference)

    def calc_pH(self):
        self.fit_p = un.correlated_values(*unmix_spectra(self.wv, self.absorbance, self.splines))
        self.F = self.fit_p[1] / self.fit_p[0]
        self.K = K_handler(self.dye, self.temp, self.sal)
        self.pH = pH_from_F(self.F, self.K)
        
    def calc_TA(self, m_sample, m_acid, C_acid):
        
        self.m_sample = m_sample
        self.m_acid = m_acid
        self.C_acid = C_acid
        
        self.TA = TA_from_pH(pH=self.pH, m_sample=self.m_sample, m_acid=self.m_acid, sal=self.sal, temp=self.temp, C_acid=self.C_acid) * 1e6
    
    def save(self, vars=['wv','dark','light_reference','light_sample','scale_factor','absorbance']):
        self.save_raw(vars=vars)
        self.save_pickle()
    
    def save_pickle(self):
        with open(self._pkl_outfile, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load_pickle(self, filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
        
    def save_raw(self, vars=['wv','dark','light_reference','light_sample','scale_factor','absorbance']):
        
        vardict = {
            'wv': self.wv,
            'dark': self.dark,
            'light_reference': self.light_reference_raw,
            'light_sample': self.light_sample_raw,
            'scale_factor': self.scale_factor,
            'absorbance': self.absorbance,
        }
        
        out = np.vstack([vardict[k] for k in vars]).T

        header = [
            f'# Config: {self.config_file}',
            f'# Time: {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}',
            f'# Temp: {self.temp:.2f}',
            f'# Sal: {self.sal:.2f}',
            f'# Dye: {self.dye}',
            f'# Splines: {self.splines}',
        ]
        
        if self.pH is not None:
            header.append(f'# pH: {self.pH:.4f}')
        
        header = '\n'.join(header + [','.join(vars)])

        np.savetxt(self._raw_outfile, out, delimiter=',', header=header, comments='')
    
    def plot(self, include=['absorbance', 'residuals', 'dark corrected', 'scale factor', 'raw']):
        if isinstance(include, str):
            include = [include]
        
        heights = {
            'raw': 1,
            'scale factor': 0.5,
            'dark corrected': 1, 
            'absorbance': 1,
            'residuals': 0.5,
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
                        axs[i].plot(self.wv, self.light_reference_raw, label='reference', color='C0')
                    if self.light_sample is not None:
                        axs[i].plot(self.wv, self.light_sample_raw, label='sample', color='C1')
                    axs[i].set_ylabel('raw counts')
                case 'scale factor':
                    axs[i].plot(self.wv, self.scale_factor, label='scale factor', color='C3')
                case 'dark corrected':
                    axs[i].plot(self.wv, self.light_reference, label='reference', color='C0')
                    axs[i].plot(self.wv, self.light_sample, label='sample', color='C1')
                    axs[i].set_ylabel('counts - dark')
                case 'absorbance':
                    axs[i].scatter(self.wv, self.absorbance, label='sample', color='k', s=1)
                    
                    if self.fit_p is not None:
                        spec_fn = make_mix_spectra(self.splines)
                        spec_components = make_mix_components(self.splines)
                        pred = spec_fn(self.wv, *unp.nominal_values(self.fit_p))
                        _, acid, base = spec_components(self.wv, *unp.nominal_values(self.fit_p))
                        axs[i].plot(self.wv, pred, color='r', lw=1, label='fit')
                        axs[i].fill_between(self.wv, 0, acid, alpha=0.2, label='acid')
                        axs[i].fill_between(self.wv, 0, base, alpha=0.2, label='base')
                    
                    axs[i].set_ylabel('absorbance')
                case 'residuals':
                    if self.fit_p is not None:
                        spec_fn = make_mix_spectra(self.splines)
                        pred = spec_fn(self.wv, *unp.nominal_values(self.fit_p))
                        resid = self.absorbance - pred
                        
                        axs[i].scatter(self.wv, resid, label='residuals', color='k', s=1)
                        axs[i].axhline(0, color=(0,0,0,0.6), lw=0.5)


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