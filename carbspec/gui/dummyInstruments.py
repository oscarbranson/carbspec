import numpy as np
from scipy.stats import norm
from carbspec.dye.splines import load_splines
from carbspec.spectro.mixture import make_mix_spectra

import time

mixture = make_mix_spectra('MCP')

class Spectrometer:
    def __init__(self):
        self.light = False
        self.channel = 0
        self.sample = False

        self.bkg = 1800 / 5  # background at 1 ms
        self.noise = 500  # noise at 1ms

        self.connected = True

        self.integration_time = 10
        
        self.wvMin = 400
        self.wvMax = 700
        self.wv = np.arange(self.wvMin, self.wvMax)

        self.light_only = np.linspace(11000, 55000, self.wv.size) * (norm.pdf(self.wv, 400, 100) + norm.pdf(self.wv, 600, 300)) * 10
        self.scale_factor = 1.5 - 0.002 * (self.wv - 400)

    def set_wavelength_range(self, val, limit):
        if limit == 'wvMin':
            self.wvMin = val
        else:
            self.wvMax = val
        self.wv = np.arange(self.wvMin, self.wvMax)

    def set_integration_time(self, integration_time):
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

    def newSample(self):
        a = np.random.uniform(.3, .4)
        f = np.random.uniform(0, 1)
        self.Abs = mixture(self.wv, a, a * f)

    def read(self):
        time.sleep(self.integration_time / 1000)
        if self.light:
            I0 = self.light_only * self.integration_time + np.random.normal(self.bkg, self.noise / self.integration_time, self.wv.size)
            if self.channel == 0:
                return I0
            elif self.channel == 1:
                I0 *= self.scale_factor
                if self.sample:
                    return I0 / 10**self.Abs
                else:
                    return I0
        else:
            return np.random.normal(self.bkg, self.noise / self.integration_time, self.wv.size)

class TempProbe:
    def __init__(self):
        self.lastTemp = self.read()
        self.connected = True

    def read(self):
        return np.random.normal(25, 2)

class BeamSwitch:
    def __init__(self):
        self.channel = 0
        self.connected = True
    
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