import numpy as np
import seabreeze
seabreeze.use('cseabreeze')
from seabreeze.spectrometers import Spectrometer as sbSpectrometer
from seabreeze.spectrometers import list_devices

def list_spectrometers():
    devices = list_devices()
    print(devices)
    return [f'{s.model} : SN-{s.serial_number}' for s in devices]
class Spectrometer(sbSpectrometer):
    def __init__(self, device):
        super().__init__(device=device)
                
        # state
        self.channel = 0
        self.light = True
        self.sample = True

        # settings
        self.wvMin = -np.inf
        self.wvMax = np.inf
        
        self.update_wv()
            
    @classmethod
    def from_serial_number(cls, serial: str | None = None):
        return super(Spectrometer, cls).from_serial_number(serial=serial)
    
    def set_wavelength_range(self, wvMin=None, wvMax=None):
        if wvMin is not None:
            self.wvMin = wvMin
        if wvMax is not None:
            self.wvMax = wvMax
            
        self.update_wv()
                
    def update_wv(self):
        wv = self.wavelengths()
        self.filter = (wv > self.wvMin) & (wv < self.wvMax)
        self.wv = wv[self.filter]     
        
    def read(self, 
             correct_dark_counts: bool = False, 
             correct_nonlinearity: bool = False
    ):
        return self.intensities(
            correct_dark_counts=correct_dark_counts,
            correct_nonlinearity=correct_nonlinearity
        )[self.filter]

        
    def disconnect(self):
        self.close()

    def set_integration_time_ms(self, integration_time_ms):
        self.integration_time_micros(integration_time_ms * 1e3)

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

    # def newSample(self):
    #     a = np.random.uniform(.3, .4)
    #     f = np.random.uniform(0, 1)
    #     self.Abs = mixture(self.wv, a, a * f)

    # def read(self, correct_dark_counts: bool = False, correct_nonlinearity: bool = False):
    #     return self.intensities(correct_dark_counts=correct_dark_counts, correct_nonlinearity=correct_nonlinearity)