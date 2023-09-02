
##########################################
# Running via Adafruit FT232H
# See: https://learn.adafruit.com/circuitpython-on-any-computer-with-ft232h
##########################################
import board
import digitalio
from .instrument import Instrument

class BeamSwitch(Instrument):
    def __init__(self, reverse_sides=False):
        self.reverse_sides = reverse_sides
        
        self.board = board

        self.position = None

        self.instrument_type = 'OceanOptics TTY Beam Switch'
        self.instrument_info = f'{self.instrument_type} controlled via {self.board.board_id}'
        
        self.connect()
        
    def connect(self):
        self.switch = digitalio.DigitalInOut(board.C7)
        self.switch.direction = digitalio.Direction.OUTPUT
        
        # toggle connection
        self.sample_cell()
        self.reference_cell()
        
        self.connected = True
        print(f'  > Connected to {self.instrument_info}')
        
    def disconnect(self):
        self.connected = False
        print(f'  > Disconnected from {self.instrument_info}')
    
    def toggle_cells(self):
        self.switch.value = not self.switch.value
        
        if self.position == 'sample':
            self.position = 'reference'
        else:
            self.position = 'sample'

    def sample_cell(self):
        if self.reverse_sides:
            self.switch.value = True
        else:
            self.switch.value = False
        self.position = 'sample'
    
    def reference_cell(self):
        if self.reverse_sides:
            self.switch.value = False
        else:
            self.switch.value = True
        self.position = 'reference'
