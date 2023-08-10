import board
import digitalio
from .instrument import Instrument

class BeamSwitch(Instrument):
    def __init__(self, reverse_sides=False):
        self.reverse_sides = reverse_sides
        
        self.board = board

        self.instrument_type = 'OceanOptics TTY Beam Switch'
        self.instrument_info = f'{self.instrument_type} controlled via {self.board.board_id}'
        
    def connect(self):
        self.switch = digitalio.DigitalInOut(board.D7)
        self.switch.direction = digitalio.Direction.OUTPUT
        
        # toggle connection
        self.switch.value = False
        self.switch.value = True
        
        self.connected = True
        print(f'Connected to {self.instrument_info}')
        
    def disconnect(self):
        self.connected = False
        print(f'Disconnected from {self.instrument_info}')
    
    def toggle_cells(self):
        self.switch.value = not self.switch.value
    
    def sample_cell(self):
        if self.reverse_sides:
            self.switch.value = True
        else:
            self.switch.value = False
    
    def reference_cell(self):
        if self.reverse_sides:
            self.switch.value = False
        else:
            self.switch.value = True
    

##########################################
# Raspberry Pi Operation
##########################################
# from gpiozero import PWMOutputDevice
# from .instrument import Instrument

# class BeamSwitch(Instrument):
#     def __init__(self, pin="GPIO14", reverse_sides=True):
#         self.pin = pin
#         self.reverse_sides = reverse_sides

#         self.instrument_type = 'OceanOptics TTY Beam Switch'
#         self.instrument_info = f'{self.instrument_type} on {self.pin}'

#     def connect(self):
#         self.switch = PWMOutputDevice(pin=self.pin, frequency=5)
#         self.connected = True
#         print(f'Connected to {self.instrument_info}')


#     def disconnect(self):
#         self.switch.close()
#         self.connected = False
#         print(f'Disconnected from {self.instrument_info}')

#     def sample_cell(self):
#         if self.reverse_sides:
#             self.switch.on()
#         else:
#             self.switch.off()
    
#     def reference_cell(self):
#         if self.reverse_sides:
#             self.switch.off()
#         else:
#             self.switch.on()
    
#     def toggle_cells(self):
#         self.switch.toggle()