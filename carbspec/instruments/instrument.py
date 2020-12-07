from serial.tools import list_ports

class Instrument:
    def __init__(self):
        self.connected = False
        self.output = None

        self.instrument_type = 'Template'

        self._com_grep = 'test'
        self._com_params = {}
    
    def find_port(self):
        found_ports = []
        for p in list_ports.grep(self._com_grep):
            found_ports.append(p)

        if len(found_ports) == 0:
            raise ValueError(f'No port found containing {self._com_grep}. Is the sensor connected?')

        if len(found_ports) > 1:
            raise ValueError('\n'.join([f'Multiple ports found containing {self._com_grep}:'] + found_ports + ['Please disconnect one of them and try again.']))
        
        return found_ports[0]

    def connect(self):
        raise NotImplementedError(f'Invalid command for {self.instrument_type}')

    def disconnect(self):
        raise NotImplementedError(f'Invalid command for {self.instrument_type}')
    
    def read(self):
        raise NotImplementedError(f'Invalid command for {self.instrument_type}')

