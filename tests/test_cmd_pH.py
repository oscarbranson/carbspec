import pytest
import pandas as pd
import shutil
from carbspec.cmd.session import pHMeasurementSession

def test_measurement_workflow(monkeypatch):
        
    monkeypatch.setattr('builtins.input', lambda _: '\n')

    meas = pHMeasurementSession(dye='MCP', config_file='tests/carbspec.cfg')

    meas.spectrometer.light_off()
    meas.collect_dark()
    
    meas.spectrometer.light_on()
    meas.spectrometer.sample_absent()

    meas.collect_scale_factor()
    
    meas.spectrometer.sample_present()

    meas.spectrometer.newSample(f=0.6)
    meas.measure_sample('test1', plot_vars='absorbance')
    
    assert True

def test_reading_pkl():
    
    pd.read_pickle('tests/testsave/MCP_summary.pkl')
    
    assert True

@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    def remove_test_dir():
        shutil.rmtree('tests/testsave')    
    request.addfinalizer(remove_test_dir)