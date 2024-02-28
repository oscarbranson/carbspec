from .spectrometer import Spectrometer
from .temperature import TempProbe

# try to import beamswitch
try:
    from .beamswitch_rpi import BeamSwitch
except:
    pass

try: 
    from .beamswitch_FT232H import BeamSwitch
except:
    pass