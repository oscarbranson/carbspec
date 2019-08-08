from PyQt5 import QtGui, QtCore
from dummyInstruments import Spectrometer
import numpy as np
from carbspec.spectro.mixture import unmix_spectra, make_mix_spectra, pH_from_F
from carbspec.dye import calc_KBPB, calc_KMCP
from carbspec.splines import load_dye_splines
import pyqtgraph as pg
from uncertainties.unumpy import nominal_values

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
        self.data = {}

        self.live = {}
        self.live['wv'] = []
        self.live['signal'] = []

        self.incremental = {}
        self.incremental['wv'] = []
        self.incremental['signal'] = []

        self.last5 = {'Sample': [''] * 5,
                      'pH': [''] * 5,
                      'Temp': [''] * 5}

        # Dict of program paramters - load from file in future?
        self.params = {}
        
        # Temperature Probe Parameters
        self.params['temp'] = {
            'calib_m': 1,
            'calib_c': 0,
            'commLink': None
            }
        # Spectrometer Parameters
        self.params['spectro'] = {
            'commLink': None,
            'integrationTime': 10,
            'nScans': 50
        }

        self.connectSpectrometer()
    
    def connectSpectrometer(self):
        self.spectrometer = Spectrometer()
        self.data['wv'] = self.spectrometer.wv

    def readSpectrometer(self, line=None, plot_mode='incremental', pbar=None, pbar_0=0):
        self.incremental['wv'] = self.data['wv']

        for i in range(self.params['spectro']['nScans']):
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

    def collectDark(self, line, plot_mode):
        self.spectrometer.light_off()
        # set pbar bar max
        self.mainWindow.setupPane.spectro['darkProgress'].setMaximum(self.params['spectro']['nScans'])
        # measure
        self.readSpectrometer(line=line, plot_mode=plot_mode, pbar=self.mainWindow.setupPane.spectro['darkProgress'])
        self.mainWindow.setupPane.spectro['scaleFactor'].setDisabled(False)

        self.data['dark'] = self.incremental['signal']

        self.mainWindow.setupPane.spectro['scaleFactor'].setDisabled(False)
        self.darkCollected = True

    def collectScaleFactor(self, lines, plot_mode):
        self.spectrometer.light_on()
        self.spectrometer.sample_absent()

        lines[0].curve.setData(y=[])
        lines[1].curve.setData(y=[])
        self.mainWindow.setupPane.graphs['scale'].lines[0].setData(y=[])

        pbar = self.mainWindow.setupPane.spectro['scaleProgress']
        pbar.setMaximum(2 * self.params['spectro']['nScans'])

        self.spectrometer.channel_0()
        self.readSpectrometer(line=lines[0], plot_mode=plot_mode, pbar=pbar, pbar_0=0)
        self.data['channel0'] = self.incremental['signal']

        self.spectrometer.channel_1()
        lines[1].setData(x=self.data['wv'])
        self.readSpectrometer(line=lines[1], plot_mode=plot_mode, pbar=pbar, pbar_0=self.params['spectro']['nScans'])
        self.data['channel1'] = self.incremental['signal']

        self.data['scaleFactor'] = self.data['channel1'] / self.data['channel0']
        self.mainWindow.setupPane.graphs['scale'].lines[0].curve.setData(x=self.data['wv'], y=self.data['scaleFactor'])
        self.scaleCollected = True  

        self.mainWindow.measurePane.collectSpectrum.setDisabled(False)

    def specChanged(self):
        self.darkCollected = False
        self.scaleCollected = False
        # disable
        self.mainWindow.setupPane.spectro['scaleFactor'].setDisabled(True)
        # reset dark spectrum progress bar
        self.mainWindow.setupPane.spectro['darkProgress'].reset()
        # reset scale factor progress bar
        self.mainWindow.setupPane.spectro['scaleProgress'].reset()

        self.mainWindow.measurePane.collectSpectrum.setDisabled(True)

    def update_parameter(self, instrument, parameter, dtype, value):
        if value == '':
            val = None
        else:
            val = dtype(value) 
        self.params[instrument][parameter] = val

        # if any spectro parameter is changed, update the dark
        if parameter in self.params['spectro'].keys():
            self.specChanged()

    def collectSpectrum(self, lines, plot_mode):
        self.spectrometer.light_on()
        self.spectrometer.sample_present()
        self.spectrometer.newSample()

        self.clearGraph(self.mainWindow.measurePane.graphs['abs'])
        self.clearGraph(self.mainWindow.measurePane.graphs['raw'])
        self.clearGraph(self.mainWindow.measurePane.graphs['resid'])

        self.mainWindow.measurePane.graphs['abs'].lines[0].setData(y=[])

        self.spectrometer.channel_0()
        self.readSpectrometer(line=lines[0], plot_mode=plot_mode)
        self.data['channel0_unscaled'] = self.incremental['signal']
        self.data['channel0'] = self.data['channel0_unscaled'] * self.data['scaleFactor']

        self.spectrometer.channel_1()
        self.readSpectrometer(line=lines[1], plot_mode=plot_mode)
        self.data['channel1'] = self.incremental['signal']

        self.data['absorption'] = np.log10((self.data['channel0'] - self.data['dark']) / (self.data['channel1'] - self.data['dark']))
        self.mainWindow.measurePane.graphs['abs'].lines[0].setData(x=self.data['wv'], y=self.data['absorption'])

        self.fitMCP()
    
    def fitMCP(self):
        splines = load_dye_splines('MCP')

        sal = 35
        temp = 25

        K_MCP = calc_KMCP(temp, sal)
        
        p, cov = unmix_spectra(self.data['wv'], self.data['absorption'], splines['acid'], splines['base'], weights=True)
        p = nominal_values(p)

        F = p[1] / p[0]

        pH = pH_from_F(F, K_MCP)

        # draw curves
        graph = self.mainWindow.measurePane.graphs['abs']
        mixture = make_mix_spectra(splines['acid'], splines['base'])
        x = self.data['wv']
        pred = mixture(x, *p)
        baseline = np.full(x.size, p[2])
        xm = p[-2] + x * p[-1]
        acid = baseline + splines['acid'](xm) * p[0]
        base = baseline + splines['base'](xm) * p[1]

        graph.lines['pred'] = pg.PlotDataItem(x=x, y=pred, pen=pg.mkPen(color=styles.colour_main, width=2, style=QtCore.Qt.DashLine))
        graph.graph.addItem(graph.lines['pred'])

        acid_color = list(styles.colour_dark) + [100]
        graph.lines['acid'] = pg.PlotCurveItem(x=x, y=acid, brush=pg.mkBrush(*acid_color), fillLevel=0.0, pen=(0,0,0,100))
        graph.graph.addItem(graph.lines['acid'])

        base_color = list(styles.colour_main) + [100]
        graph.lines['base'] = pg.PlotCurveItem(x=x, y=base, brush=pg.mkBrush(*base_color), fillLevel=0.0, pen=(0,0,0,100))
        graph.graph.addItem(graph.lines['base'])

        # plot residual
        rgraph = self.mainWindow.measurePane.graphs['resid']
        rgraph.lines[0].setData(x=x, y=self.data['absorption'] - pred)
    
    
    def clearGraph(self, graph):
        for line in graph.lines.values():
            line.setData(y = [])
    
    def writeSpectra(self, parameter_list):
        pass

    def writeResult(self, parameter_list):
        pass