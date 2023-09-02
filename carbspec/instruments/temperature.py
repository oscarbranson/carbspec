import numpy as np
# from pymodbus.client import ModbusSerialClient
import minimalmodbus
import time

from .instrument import Instrument

class TempProbe(Instrument):
    def __init__(self, averaging_period=2, m=1, c=0):
        super().__init__()
        
        self._com_grep = 'OS-MINIUSB'
        self._com_port = self.find_port()
        self._com_unit = 255  # communicates with any connected sensor

        self.m = m
        self.c = c

        self.instrument_type = 'IR Temperature Probe'
        self.instrument_info = f'{self._com_port.product} {self.instrument_type} (SN: {self._com_port.serial_number}) on {self._com_port.device}'

        self._com_params = {
            "port": self._com_port.device,
            "method": 'rtu',
            "baudrate": 9600,
            "timeout": 10,
            "parity": 'N',
            "stopbit": 1,
            "bytesize": 8    
        }

        self.connect()
        self.set_averaging_period(averaging_period)
        self.averaging_period = self.get_averaging_period()
        self.read()
   
    def connect(self):
        self.sensor = minimalmodbus.Instrument(self._com_params['port'], self._com_unit)
        
        self.sensor.serial.baudrate = self._com_params['baudrate']
        self.sensor.serial.timeout = self._com_params['timeout']
        self.sensor.serial.parity = self._com_params['parity']
        self.sensor.serial.stopbits = self._com_params['stopbit']
        self.sensor.serial.bytesize = self._com_params['bytesize']
        
        self.connected = True

        print(f'  > Connected to {self.instrument_info}')

    def disconnect(self):
        self.sensor.serial.close()
        self.connected = False

        print(f'  > Disconnected from {self.instrument_info}')

    def read(self):
        """
        Read temperature in Celcius.
        """
        self._check_connected()
        
        return np.round(self.sensor.read_register(0x0B, number_of_decimals=1) * self.m + self.c, 2)

    # sensor-specific functions
    def set_averaging_period(self, seconds=0.1):
        """
        Set sensor averaging period in seconds.
        """
        self._check_connected()
        response = self.sensor.write_register(registeraddress=0x0A, value=seconds, number_of_decimals=1)
        self.averaging_period = seconds
        time.sleep(0.1)
    
    def get_averaging_period(self):
        """
        Returns sensor averaging period in seconds.
        """
        return self.sensor.read_register(registeraddress=0x0A, number_of_decimals=1)
    

# class TempProbe(Instrument):
#     def __init__(self):
#         super().__init__()
        
#         self._com_grep = 'OS-MINIUSB'
#         self._com_port = self.find_port()
#         self._com_unit = 255  # communicates with any connected sensor

#         self.instrument_type = 'IR Temperature Probe'
#         self.instrument_info = f'{self._com_port.product} {self.instrument_type} (SN: {self._com_port.serial_number}) on {self._com_port.device}'

#         self._com_params = {
#             "port": self._com_port.device,
#             "method": 'rtu',
#             "baudrate": 9600,
#             "timeout": 10,
#             "parity": 'N',
#             "stopbit": 1,
#             "bytesize": 8    
#         }

#         self.connect()
#         self.read()

        
#     def connect(self):
#         self.sensor = ModbusSerialClient(**self._com_params)
#         self.connected = True

#         print(f'Connected to {self.instrument_info}')

#     def disconnect(self):
#         self.sensor.close()
#         self.connected = False

#         print(f'Disconnected from {self.instrument_info}')

#     def read(self, n=1):
#         """
#         Read temperature in Celcius.
#         """
#         self._check_connected()
#         self.output = self.sensor.read_holding_registers(address=0x0B, count=n, unit=self._com_unit)
#         return np.array(self.output.registers) / 10

#     # sensor-specific functions
#     def set_averaging_period(self, seconds=0.1):
#         """
#         Set sensor averaging period in seconds.
#         """
#         self._check_connected()
#         response = self.sensor.write_register(address=0x0A, value=int(seconds * 10), unit=self._com_unit)
    
#     def get_averaging_period(self):
#         """
#         Returns sensor averaging period in seconds.
#         """
#         return self.sensor.read_holding_registers(address=0x0A, count=1, unit=self._com_unit).registers[0] / 10
