##########################################
# Running on a Raspberry Pi
##########################################
from gpiozero import PWMOutputDevice
from .instrument import Instrument

class BeamSwitch(Instrument):
    def __init__(self, pin="GPIO14", reverse_sides=True):
        self.pin = pin
        self.reverse_sides = reverse_sides

        self.instrument_type = 'OceanOptics TTY Beam Switch'
        self.instrument_info = f'{self.instrument_type} on {self.pin}'

    def connect(self):
        self.switch = PWMOutputDevice(pin=self.pin, frequency=5)
        self.connected = True
        print(f'  > Connected to {self.instrument_info}')


    def disconnect(self):
        self.switch.close()
        self.connected = False
        print(f'  > Disconnected from {self.instrument_info}')

    def toggle_cells(self):
        self.switch.value = not self.switch.value
    
    def sample_cell(self):
        if self.reverse_sides:
            self.switch.on()
        else:
            self.switch.off()
    
    def reference_cell(self):
        if self.reverse_sides:
            self.switch.off()
        else:
            self.switch.on()
    
    def toggle_cells(self):
        self.switch.toggle()