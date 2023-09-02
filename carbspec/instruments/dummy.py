import numpy as np
from scipy.stats import norm
from carbspec.dye.splines import load_splines
from carbspec.spectro.mixture import make_mix_spectra

import time

default_splines = 'MCP_Cam1'
 
class Spectrometer:
    def __init__(self, **kwargs):
        self.light = False
        self.channel = 0
        self.sample = False

        self.bkg = 1800 / 5  # background at 1 ms
        self.noise = 500  # noise at 1ms

        self.set_splines(default_splines)
        
        self.connected = True

        self.integration_time = 10
        
        self.wvMin = 400
        self.wvMax = 700
        self.wv = np.arange(self.wvMin, self.wvMax, dtype=float)

        self.light_only = np.linspace(11000, 55000, self.wv.size) * (norm.pdf(self.wv, 400, 100) + norm.pdf(self.wv, 600, 300)) * 10
        self.scale_factor = 1.5 - 0.002 * (self.wv - 400)

        self.reference_cell = self.channel_0
        self.sample_cell = self.channel_1

        self.newSample()
        # self.close = self.disconnect
        print('  > Connected to dummy Spectrometer')

    def set_wavelength_range(self, wvMin: int | float = None, wvMax: int | float = None):
        if wvMin is not None:
            self.wvMin = wvMin
        if wvMax is not None:
            self.wvMax = wvMax
            
        self.update_wv()
                
    def update_wv(self):
        wv = np.arange(self.wvMin, self.wvMax, dtype=float)
        self.filter = (wv >= self.wvMin) & (wv <= self.wvMax)
        self.wv = wv[self.filter]
        
        self.newSample()
        self.light_only = np.linspace(11000, 55000, self.wv.size) * (norm.pdf(self.wv, 400, 100) + norm.pdf(self.wv, 600, 300)) * 10
        self.scale_factor = 1.5 - 0.002 * (self.wv - 400)

    def set_splines(self, splines):
        self.splines = splines
        self.mixture = make_mix_spectra(splines)

    def set_integration_time_ms(self, integration_time):
        self.integration_time = integration_time

    def channel_0(self):
        self.channel = 0

    def channel_1(self):
        self.channel = 1

    def light_on(self):
        self.light = True

    def light_off(self):
        self.light = False

    def sample_present(self):
        self.sample = True

    def sample_absent(self):
        self.sample = False

    def newSample(self, f=None):
        a = np.random.uniform(.3, .4)
        if f is None:
            f = np.random.uniform(0.4, 0.6)
        self.Abs = self.mixture(self.wv, a, a * f)

    def read(self):
        time.sleep(self.integration_time / 1000)
        bkg = np.random.normal(self.bkg, self.noise / self.integration_time, self.wv.size)
        if self.light:
            I0 = self.light_only * self.integration_time
            if self.channel == 0:
                return I0
            elif self.channel == 1:
                I0 *= self.scale_factor
                if self.sample:
                    return I0 / 10**self.Abs + bkg
                else:
                    return I0 + bkg
        else:
            return bkg

class TempProbe:
    def __init__(self, **kwargs):
        self.lastTemp = self.read()
        self.connected = True
        print('  > Connected to dummy TempProbe')

    def read(self):
        return np.random.normal(25, 2)

class BeamSwitch:
    def __init__(self, **kwargs):
        self.channel = 0
        self.connected = True
        
        self.reference_cell = self.channel_0
        self.sample_cell = self.channel_1
        
        print('  > Connected to dummy BeamSwitch')
    
    def switch(self):
        if self.channel == 0:
            self.channel = 1
        else:
            self.channel = 0
    
    def channel_0(self):
        self.channel = 0
    
    def channel_1(self):
        self.channel = 1
        

class LightSource:
    def __init__(self):
        self.on = True
        self.connected = True

    def turn_on(self):
        self.on = True

    def turn_off(self):
        self.on = False