import os
import pkg_resources as pkgrs
import numpy as np
import pandas as pd
from configparser import ConfigParser

import matplotlib.pyplot as plt
import uncertainties as un
import uncertainties.unumpy as unp

from carbspec.spectro.spectrum import Spectrum, calc_pH
from carbspec.alkalinity import calc_acid_strength, TA_from_pH

from pathlib import Path

def rebase_path(path, preserve_from, new_directory):
    """
    Function to rebase a path to a new directory, preserving the path up to a certain point.
    
    Parameters
    ----------
    path : str or Path
        The path to rebase.
    preserve_from : str
        The string to preserve in the path.
    new_directory : str or Path
        The new directory to rebase the path to.
        
    Returns
    -------
    Path
        The rebased path.
        
    """
    path = Path(path)
    new_directory = Path(new_directory)
    
    parts = path.parts
    try:
        idx = parts.index(preserve_from)
        return new_directory.joinpath(*parts[idx:])
    except ValueError:
        raise ValueError(f"Could not find {preserve_from} in {path}")

class pHReprocess:
    def __init__(self, dye='MCP', config_file=None, root_dir='.', savedir=None, plotting=True, save=True):
        
        self.dye = dye
        
        if config_file is None:
            config_file = pkgrs.resource_filename('carbspec', '/cmd/resources/carbspec.cfg')
        self.config_file = config_file
        self.readConfig()
        
        print('Recalling Measurement Session')
        print(f'  > Config file: {self.config_file}')
        
        self.plotting = plotting
        
        if savedir is None:
            savedir = self.config['savedir']
        self.savedir = savedir
        os.makedirs(self.savedir, exist_ok=True)
        
        # Spectra Saving
        self.save = save
        if self.save:
            print(f'  > Saving data to {self.savedir}')
        self._rawdir = os.path.join(self.savedir, 'reprocess_raw')
        os.makedirs(self._rawdir, exist_ok=True)
        self._pkldir = os.path.join(self.savedir, 'reprocess_pkl')
        os.makedirs(self._pkldir, exist_ok=True)
        self._pkl_outfile = None
        self._dat_outfile = None
        
        # Summary File Saving
        self.orig_summary_dat = os.path.join(self.savedir, f"{self.dye}_summary.dat")
        self.orig_summary_pkl = os.path.join(self.savedir, f"{self.dye}_summary.pkl")

        self.summary_dat = os.path.join(self.savedir, f"reprocess_{self.dye}_summary.dat")
        self.summary_pkl = os.path.join(self.savedir, f"reprocess_{self.dye}_summary.pkl")
        
        if os.path.exists(self.orig_summary_pkl):
            self.load_data_table(self.orig_summary_pkl)
            self._new_data_table = False
        elif os.path.exists(self.orig_summary_dat):
            self.load_data_table(self.orig_summary_dat)
            self._new_data_table = False
        else:
            raise FileNotFoundError('No summary file found.')
        
        print('  --> Ready!')

    def load_data_table(self, file):
        if '.pkl' in file:
            self.data_table = pd.read_pickle(file)
        elif '.dat' in file:
            dat = pd.read_csv(file, parse_dates=['timestamp'])
            dat.set_index('timestamp', inplace=True)
            for i, r in dat.iterrows():
                dat.loc[i, 'spectra'] = Spectrum.load(r['pkl_file'])
            self.data_table = dat
        else:
            ValueError('File must be a .dat or .pkl file.')

        print(f'  > Loaded existing data table from {file}')
            
    def readConfig(self):
        self._config = ConfigParser()
        self._config.read(self.config_file)
        self.config = self._config[self.dye]
    
    def save_spectrum(self):
        self.spectrum.save(dat_file=self._dat_outfile, pkl_file=self._pkl_outfile)
            
    def save_summary(self):
        exclude = ['spectra']
        cols = [c for c in self.data_table.columns if c not in exclude]

        if not os.path.exists(self.summary_dat):
            header = ','.join(cols) + '\n'
            with open(self.summary_dat, 'w+') as f:
                f.write(header)
        
        self.data_table.loc[[self.timestamp], cols].to_csv(self.summary_dat, header=False, index=False, mode='a')
        
        # if not os.path.exists(self.summary_dat):
        #     header = 'datetime,sample,dye,sal,temp,K,F,pH\n'
        #     with open(self.summary_dat, 'w+') as f:
        #         f.write(header)

        # data = f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')},{self.sample},{self.dye},{self.sal:.2f}, {self.temp:.2f},{self.spectrum.K:.4e},{self.spectrum.F:.4e},{self.spectrum.pH:.4f}\n"
        
        # with open(self.summary_dat, 'a') as f:
        #     f.write(data)
        
        self.data_table.to_pickle(self.summary_pkl)

class reprocess_TA:
    def __init__(self, TA_path):
        self.dat = pd.read_pickle(TA_path + '/BPB_summary.pkl')
        self.weights = pd.read_excel(TA_path + '/TA_weights.ods').dropna(subset=['sample'])
        
        self.dat['acid_batch'] = 1
        self.dat['C_acid'] = self.dat['C_acid'].astype('object')
    
    def rebase_path(self, preserve_from, new_directory):
        for i, r in self.dat.iterrows():
            self.dat.loc[i, 'dat_file'] = rebase_path(r['dat_file'], preserve_from, new_directory)
            self.dat.loc[i, 'pkl_file'] = rebase_path(r['pkl_file'], preserve_from, new_directory)
    
    def separate_sessions(self, gap='2hr'):
        self.dat['session_number'] = np.cumsum(self.dat.index.diff() > gap)
    
    def identify_CRM(self, CRM_id, CRM_TA=2199.32, CRM_sal=33.237):
        CRM_ind = self.dat['sample'].str.contains(CRM_id)
        
        self.dat.loc[CRM_ind,'CRM_TA'] = CRM_TA
        self.dat.loc[CRM_ind,'CRM_sal'] = CRM_sal
    
    def calc_acid_strength(self):
        CRM_ind = self.dat['CRM_TA'].notna()

        CRM_sub = self.dat.loc[CRM_ind]

        for i, r in CRM_sub.iterrows():
            c_acid = calc_acid_strength(
                crm_alk=r['CRM_TA'], 
                pH=r['pH'], 
                m0=r['m_sample'], 
                m=r['m_acid'], 
                sal=r['CRM_sal'], 
                temp=r['temp']
            )
            self.dat.loc[i, 'CRM_C_acid'] = c_acid
            
    def acid_changed_on(self, datetimestring):
        self.dat.loc[self.dat.index > datetimestring, 'acid_batch'] += 1
            
    def interpolate_acid_strength(self, start_datetime, end_datetime, poly_order=1, plot=False):
        ind = (self.dat.index > start_datetime) & (self.dat.index < end_datetime)

        session = self.dat.loc[ind]

        session_start = session.index.min()
        time_axis = (session.index - session_start).total_seconds()

        na_ind = session['CRM_C_acid'].notna()

        p, cov = np.polyfit(time_axis[na_ind], session.loc[na_ind, 'CRM_C_acid'], poly_order, cov=True)
        up = un.correlated_values(p, cov)

        pred_C = np.polyval(up, (session.index - session_start).total_seconds())

        self.dat['C_acid'] = self.dat['C_acid'].astype('object')
        self.dat.loc[session.index, 'C_acid'] = pred_C
        
        if plot:
            sub = session.loc[na_ind]
            plt.scatter(sub.index, sub['CRM_C_acid'], label='Measured')
            plt.plot(session.index, unp.nominal_values(pred_C), label='Interpolated')
            plt.fill_between(session.index, unp.nominal_values(pred_C) - unp.std_devs(pred_C), unp.nominal_values(pred_C) + unp.std_devs(pred_C), alpha=0.5)
            
    def calc_TA(self):
        self.dat['TA_new'] = TA_from_pH(
            pH=self.dat.pH,
            m_sample=self.dat.m_sample,
            m_acid=self.dat.m_acid, 
            C_acid=self.dat.C_acid,
            sal=self.dat.sal,
            temp=self.dat.temp) * 1e6


        