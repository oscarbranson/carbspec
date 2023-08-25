import pytest
import pandas as pd
import shutil
import datetime as dt
import time
import pyperclip
from carbspec.cmd.session import TAMeasurementSession
from carbspec.cmd.utils import get_TA_weight_template

def user_input_TA_weights(*args, **kwargs):
    file = 'tests/testsave/TA_weights.ods'
    dat = pd.read_excel(file)
    
    timestamp = pd.to_datetime(pyperclip.paste())
        
    dat.loc[0, 'timestamp'] = timestamp
    dat.set_index('timestamp', inplace=True)

    dat.loc[timestamp, '+sample'] = 0
    dat.loc[timestamp, '+acid'] = 0
    dat.loc[timestamp, 'm_sample'] = 50.0
    dat.loc[timestamp, 'm_acid'] = 1.5
    dat.loc[timestamp, 'C_acid'] = 0.1
    
    writer = pd.ExcelWriter(file, engine='odf', datetime_format='YYYY-MM-DD HH:MM:SS')
    dat.to_excel(writer)
    writer.close()
    
    time.sleep(0.1)
    
    return '\n'
    

def test_measurement_workflow(monkeypatch):
        
    monkeypatch.setattr('builtins.input', lambda _: '\n')

    meas = TAMeasurementSession(dye='BPB', config_file='tests/carbspec.cfg')
    
    meas.spectrometer.set_splines(meas.config.get('splines'))
    
    meas.spectrometer.light_off()
    meas.collect_dark()
    
    meas.spectrometer.light_on()
    meas.spectrometer.sample_absent()
    meas.collect_scale_factor()


    monkeypatch.setattr('builtins.input', user_input_TA_weights)
    
    meas.spectrometer.sample_present()
    meas.spectrometer.newSample(f=0.6)
    
    get_TA_weight_template(meas.savedir, overwrite=True)
    time.sleep(0.3)
    
    meas.measure_sample('test1', plot_vars='absorbance')
    
    assert True

def test_reading_pkl():
    
    pd.read_pickle('tests/testsave/BPB_summary.pkl')
    
    assert True

@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    def remove_test_dir():
        shutil.rmtree('tests/testsave')    
    request.addfinalizer(remove_test_dir)
