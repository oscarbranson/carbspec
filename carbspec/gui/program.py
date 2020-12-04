from PyQt5 import QtGui, QtCore
from dummyInstruments import Spectrometer
import numpy as np
from carbspec.spectro.mixture import unmix_spectra, make_mix_spectra, pH_from_F
from carbspec.dye import K_handler
from carbspec.dye.splines import load_splines
import pyqtgraph as pg
import uncertainties as un
from uncertainties.unumpy import nominal_values, std_devs
from configparser import ConfigParser
import pkg_resources as pkgrs

import pandas as pd

import styles

class Program:
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow

        self.commSpectrometer = None
        self.commTemperature = None
        self.commSwitch = None

        self.collectionMode = 'pH'
        self.darkCollected = False
        self.scaleCollected = False
        
        # data placeholder
        dataColumns = ['Sample', 'dye', 'a', 'b', 'bkg', 'c', 'm', 'F', 'Temp', 'Sal', 'K', 'pH']
        self.data = {k: None for k in dataColumns}
        self.data['Sample'] = 'SampleName'
        self.data['Sal'] = 35
        self.data['Temp'] = 25
        self.data['dye'] = 'MCP'

        self.df = pd.DataFrame(columns=dataColumns)

        self.live = {}
        self.live['wv'] = []
        self.live['signal'] = []

        self.incremental = {}
        self.incremental['wv'] = []
        self.incremental['signal'] = []

        self.last5 = {'Sample': [''] * 5,
                      'pH': [''] * 5,
                      'Temp': [''] * 5}

        # # Dict of program paramters - load from file in future?
        # self.params = {}
        
        # # Temperature Probe Parameters
        # self.params['Temp'] = {
        #     'temp_m': 1,
        #     'temp_c': 0,
        #     'commLink': None
        #     }
        # # Spectrometer Parameters
        # self.params['spectro'] = {
        #     'commLink': None,
        #     'integrationTime': 10,
        #     'nScans': 50
        # }

        self._rsrcpath = pkgrs.resource_filename('carbspec', '/gui/resources/')
        self._cfgfile = self._rsrcpath + 'carbspec.cfg'

        self.readConfig()

        self.connectSpectrometer()

        self.modeSet(self.config.get('mode'))

    # def loadConfig(self):
        
        # self.params['spectro']['integrationTime'] = self.config['Last'].get('integrationTime')
        # self.params['spectro']['nScans'] = self.config['Last'].get('nScans')

        # self.params['Temp']['temp_m'] = self.config['Last'].get('temp_m')
        # self.params['Temp']['temp_c'] = self.config['Last'].get('temp_c')

        # self.saveDir = self.config['Last'].get('saveDir')
        # self.dye = self.config['Last'].get('mode')

    def readConfig(self):
        self._config = ConfigParser()
        self._config.read(self._cfgfile)
        self.config = self._config['LAST']

    def writeConfig(self):
        with open(self._cfgfile, 'w') as f:
            self._config.write(f)

    def updateConfig(self, parameter, value):
        if parameter in self._config['DEFAULT']:
            self._config.set('LAST', parameter, str(value))
        
        self.writeConfig()

    def findSpectrometer(self):
        return ['Spec1', 'Spec2']
    
    def connectSpectrometer(self):
        self.spectrometer = Spectrometer()
        self.data['wv'] = self.spectrometer.wv

    def readSpectrometer(self, line=None, plot_mode='incremental', pbar=None, pbar_0=0):
        self.incremental['wv'] = self.data['wv']

        for i in range(self.config.getint('nScans')):
            meas = self.spectrometer.read()

            if i == 0:
                self.incremental['signal'] = meas
            else:
                self.incremental['signal'] *= i / (i + 1)
                self.incremental['signal'] += meas / (i + 1)
        
            if line is not None:
                if plot_mode == 'incremental':
                    line.curve.setData(x=self.data['wv'], y=self.incremental['signal'])
                elif plot_mode == 'live':
                    line.curve.setData(y=meas)

            if pbar is not None:
                pbar.setValue(i + 1 + pbar_0)

            QtGui.QApplication.processEvents()  # required to update plot

    def readTemp(self):
        return np.random.uniform(22,27)

    # def readSampleName(self):
    #     print(self.mainWindow.measurePane.sampleName.)

    def collectDark(self, line, plot_mode):
        
        self.specChanged()
        self.spectrometer.light_off()
        # set pbar bar max
        self.mainWindow.setupPane.spectro['darkProgress'].setMaximum(self.config.getint('nScans'))
        # measure
        self.readSpectrometer(line=line, plot_mode=plot_mode, pbar=self.mainWindow.setupPane.spectro['darkProgress'])
        self.mainWindow.setupPane.spectro['scaleFactor'].setDisabled(False)

        self.data['dark'] = self.incremental['signal']

        self.mainWindow.setupPane.spectro['scaleFactor'].setDisabled(False)
        self.darkCollected = True

    def collectScaleFactor(self, lines, plot_mode):
        self.spectrometer.light_on()
        self.spectrometer.sample_absent()

        self.clearGraph(self.mainWindow.setupPane.graphChannels)
        self.clearGraph(self.mainWindow.setupPane.graphScale)

        pbar = self.mainWindow.setupPane.spectro['scaleProgress']
        pbar.setMaximum(2 * self.config.getint('nScans'))

        self.spectrometer.channel_0()
        self.readSpectrometer(line=lines[0], plot_mode=plot_mode, pbar=pbar, pbar_0=0)
        self.data['channel0'] = self.incremental['signal']

        self.spectrometer.channel_1()
        lines[1].setData(x=self.data['wv'])
        self.readSpectrometer(line=lines[1], plot_mode=plot_mode, pbar=pbar, pbar_0=self.config.getint('nScans'))
        self.data['channel1'] = self.incremental['signal']

        self.data['scaleFactor'] = self.data['channel1'] / self.data['channel0']
        self.mainWindow.setupPane.graphScale.lines[0].curve.setData(x=self.data['wv'], y=self.data['scaleFactor'])
        self.scaleCollected = True

        self.mainWindow.measurePane.collectSpectrum.setDisabled(False)

    def specChanged(self):
        self.darkCollected = False
        self.scaleCollected = False

        self.clearGraph(self.mainWindow.setupPane.graphDark)
        self.clearGraph(self.mainWindow.setupPane.graphChannels)
        self.clearGraph(self.mainWindow.setupPane.graphScale)
        
        # disable
        self.mainWindow.setupPane.spectro['scaleFactor'].setDisabled(True)
        # reset dark spectrum progress bar
        self.mainWindow.setupPane.spectro['darkProgress'].reset()
        # reset scale factor progress bar
        self.mainWindow.setupPane.spectro['scaleProgress'].reset()

        self.mainWindow.measurePane.collectSpectrum.setDisabled(True)

    def update_parameter(self, instrument, parameter, dtype, value):
        if value == '' or value == '.':
            val = None
        else:
            val = dtype(value) 
        if val is not None:
            self.updateConfig(parameter, val)

        # if any spectro parameter is changed, update the dark
        if parameter in ['integrationTime', 'nScans', 'wvMin', 'wvMax']:
            self.specChanged()
        
        if parameter == 'integrationTime' and val is not None:
            self.spectrometer.set_integration_time(val)
        
        if parameter in ['wvMin', 'wvMax']:
            self.spectrometer.set_wavelength_range(val, parameter)
            self.data['wv'] = self.spectrometer.wv
        
        if parameter in self.data:
            self.data[parameter] = val

    def collectSpectrum(self, lines, plot_mode):
        self.mainWindow.measurePane.collectSpectrum.setDisabled(True)
        self.spectrometer.light_on()
        self.spectrometer.sample_present()
        self.spectrometer.newSample()

        self.clearGraph(self.mainWindow.measurePane.graphAbs)
        self.clearGraph(self.mainWindow.measurePane.graphRaw)
        self.clearGraph(self.mainWindow.measurePane.graphResid)
        
        pbar = self.mainWindow.measurePane.collectionPBar
        pbar.setMaximum(2 * self.config.getint('nScans'))
        
        self.spectrometer.channel_0()
        self.readSpectrometer(line=lines[0], plot_mode=plot_mode,
                              pbar=pbar, pbar_0=0)
        self.data['channel0_unscaled'] = self.incremental['signal']
        self.data['channel0'] = self.data['channel0_unscaled'] * self.data['scaleFactor']

        t0 = self.readTemp()
        self.spectrometer.channel_1()
        self.readSpectrometer(line=lines[1], plot_mode=plot_mode,
                              pbar=pbar, pbar_0=self.config.getint('nScans'))
        self.data['channel1'] = self.incremental['signal']
        t1 = self.readTemp()

        self.data['absorption'] = np.log10((self.data['channel0'] - self.data['dark']) / (self.data['channel1'] - self.data['dark']))
        self.mainWindow.measurePane.graphAbs.lines[0].setData(x=self.data['wv'], y=self.data['absorption'])

        self.data['Temp'] = np.mean([t0, t1])

        self.fitSpectrum()

        self.mainWindow.measurePane.collectSpectrum.setDisabled(False)


    def fitSpectrum(self):

        self.data['K'] = K_handler(self.data['dye'], self.data['Temp'], self.data['Sal'])
        
        p, cov = unmix_spectra(self.data['wv'], self.data['absorption'], self.data['dye'])

        self.p = un.correlated_values(p, cov)
        self.data.update({k: v for k, v in zip(['a', 'b', 'bkg', 'c', 'm'], self.p)})

        self.data['F'] = self.p[1] / self.p[0]

        self.data['pH'] = pH_from_F(self.data['F'], self.data['K'])
        
        # self.storeResult(K, F, pH)
        self.storeResult()
        self.updateFitGraph()

    # def storeResult(self, K, F, pH):
    def storeResult(self):
        i = np.nanmax([0, self.df.index.max() + 1])
        self.df.loc[i] = np.nan

        for k in ['Sample', 'dye', 'a', 'b', 'bkg', 'c', 'm', 'F', 'Temp', 'Sal', 'K', 'pH']:
            self.df.loc[i, k] = self.data[k]

        # self.df.loc[i, ['a', 'b', 'bkg', 'c', 'm']] = self.p
        # self.df.loc[i, ['dye']] = self.data['dye']
        # self.df.loc[i, ['K', 'F', 'pH']] = K, F, pH
        # self.df.loc[i, 'Sample'] = self.data['Sample']

    def refitSpectrum(self):
        self.df.drop(self.df.index.max(), inplace=True)
        self.clearFitGraph()
        self.fitSpectrum()

    def updateFitGraph(self):
        p = nominal_values(self.p)
        # draw curves
        graph = self.mainWindow.measurePane.graphAbs
        mixture = make_mix_spectra(self.data['dye'])
        x = self.data['wv']
        pred = mixture(x, *p)
        baseline = np.full(x.size, p[2])
        xm = p[-2] + x * p[-1]
        acid = baseline + self.splines['acid'](xm) * p[0]
        base = baseline + self.splines['base'](xm) * p[1]

        graph.lines['pred'] = pg.PlotDataItem(x=x, y=pred, pen=pg.mkPen(color=styles.colour_main, width=2, style=QtCore.Qt.DashLine))
        graph.addItem(graph.lines['pred'])

        acid_color = list(styles.colour_dark) + [100]
        graph.lines['acid'] = pg.PlotCurveItem(x=x, y=acid, brush=pg.mkBrush(*acid_color), fillLevel=0.0, pen=(0,0,0,100))
        graph.addItem(graph.lines['acid'])

        base_color = list(styles.colour_main) + [100]
        graph.lines['base'] = pg.PlotCurveItem(x=x, y=base, brush=pg.mkBrush(*base_color), fillLevel=0.0, pen=(0,0,0,100))
        graph.addItem(graph.lines['base'])

        # plot residual
        rgraph = self.mainWindow.measurePane.graphResid
        rgraph.lines[0].setData(x=x, y=self.data['absorption'] - pred)

    def clearFitGraph(self):
        graph = self.mainWindow.measurePane.graphAbs
        graph.lines['pred'].setData(y=[])
        graph.lines['acid'].setData(y=[])
        graph.lines['base'].setData(y=[])
        rgraph = self.mainWindow.measurePane.graphResid
        rgraph.lines[0].setData(y=[])
    
    def modeSet(self, i):
        modes = ['MCP', 'BPB']
        if i in modes:
            self.data['dye'] = i
        elif isinstance(i, int):
            self.data['dye'] = modes[i]
        else:
            ValueError('i must be an integer or a string')

        self.splines = load_splines(self.data['dye'])

        if 'absorption' in self.data:
            self.clearFitGraph()
            self.fitSpectrum()

        print(self.data['dye'])
    
    def clearGraph(self, graph):
        for line in graph.lines.values():
            line.setData(y = [])
    
    def writeSpectra(self, parameter_list):
        pass

    def writeResult(self, parameter_list):
        pass