import PyQt5.QtWidgets as qt
import PyQt5.QtGui as qg
from PyQt5 import QtCore
import pyqtgraph as pg
import numpy as np
from functools import partial

from carbspec.instruments.spectrometer import list_spectrometers

import styles
from graph import GraphItem
from statusLED import LEDIndicator

def dummyConnect(*args, **kwargs):
    """
    Dummy function for identifying connection content.
    """
    for arg in args:
        print(arg, type(arg))
    for k, v in kwargs.items():
        print(k, v, type(v))

def makeDummy():
    dummy = qt.QFrame()
    dummy.setMinimumHeight(200)
    rgb = np.random.randint(0,255,3)
    dummy.setStyleSheet ( "background-color: rgb({}, {}, {})".format(*rgb))

    return dummy

def Hline():
    line = qt.QFrame()
    line.setFrameShape(qt.QFrame.HLine)
    line.setFrameShadow(qt.QFrame.Sunken)
    return line

class setupPane:
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow

        self.program = self.mainWindow.program

        self.layout = qt.QGridLayout()
        self.layout.setColumnStretch(0,1)
        self.layout.setColumnStretch(1,1)
        self.layout.setRowStretch(0,3)
        self.layout.setRowStretch(1,3)
        self.layout.setRowStretch(2,1)

        self.mainWindow.setupTab.setLayout(self.layout)

        self.graphs = {}
        self.spectro = {}
        self.temp = {}

        self.spectrometer(0, 0, 1, 1)
        self.temperature(1, 0, 1, 1)
        self.filePaths(2, 0, 1, 1)
        self.setupGraphs(0, 1, 3, 1)
        
        self.connections()
        self.setLastConfig()
        
    def refreshSpectrometers(self):
        print('refreshing spectrometers')
        self.spectro['commLink'].clear()
        self.program.spectrometers = list_spectrometers()
        for spec in self.program.spectrometers:
            self.spectro['commLink'].addItem(spec)
        self.setLastConfig()
            
    def setLastConfig(self):
        if self.program.config.get('spectrometer') in self.program.spectrometers:
            self.program.connectSpectrometer(self.program.config.get('spectrometer'))

    def spectrometer(self, *pos):
        
        self.spectroPane = qt.QWidget()
        self.spectroLayout = qt.QVBoxLayout()
        self.spectroPane.setLayout(self.spectroLayout)

        self.spectroLayout.addWidget(qt.QLabel("USB Spectrometer", objectName="title"))
        self.spectroLayout.addWidget(Hline())

        optPane = qt.QWidget()
        optGrid = qt.QGridLayout(optPane)

        current_row = 0

        # spectrometer connection
        commLink = qt.QComboBox()
        self.spectro['commLink'] = commLink
        self.refreshSpectrometers()
        optGrid.addWidget(qt.QLabel('Spectrometers:'), current_row, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        optGrid.addWidget(commLink, current_row, 1, 1, 3)

        specConnectButton = qt.QPushButton('Connect')
        self.spectro['specConnectButton'] = specConnectButton
        optGrid.addWidget(specConnectButton, current_row, 4, 1, 1)
        
        statusSpectrometer = LEDIndicator()
        self.spectro['statusLED'] = statusSpectrometer
        optGrid.addWidget(statusSpectrometer, current_row, 5, 1, 1)
        
        current_row += 1
        
        specRefreshButton = qt.QPushButton('Refresh')
        self.spectro['specRefreshButton'] = specRefreshButton
        optGrid.addWidget(specRefreshButton, current_row, 4, 1, 1)
        
        # spectrometer setup
        integTime = qt.QLineEdit(self.program.config.get('integrationTime'))
        integTime.setValidator(qg.QIntValidator())
        self.spectro['integrationTime'] = integTime
        optGrid.addWidget(qt.QLabel('Integration Time (ms):'), current_row, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        optGrid.addWidget(integTime, current_row, 1, 1, 1)

        nScans = qt.QLineEdit(self.program.config.get('nScans'))
        nScans.setValidator(qg.QIntValidator())
        self.spectro['nScans'] = nScans
        optGrid.addWidget(qt.QLabel('Replicate Scans:'), current_row, 2, 1, 1, alignment=QtCore.Qt.AlignRight)
        optGrid.addWidget(nScans, current_row, 3, 1, 1)
        current_row += 1

        # wavelength range
        wvMin = qt.QLineEdit(self.program.config.get('wvMin'))
        wvMin.setValidator(qg.QIntValidator())
        self.spectro['wvMin'] = wvMin
        optGrid.addWidget(qt.QLabel('Wavelength Min'), current_row, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        optGrid.addWidget(wvMin, current_row, 1, 1, 1)

        wvMax = qt.QLineEdit(self.program.config.get('wvMax'))
        wvMax.setValidator(qg.QIntValidator())
        self.spectro['wvMax'] = wvMax
        optGrid.addWidget(qt.QLabel('Wavelength Max'), current_row, 0, 1, 1, alignment=QtCore.Qt.AlignRight)
        optGrid.addWidget(wvMax, current_row, 3, 1, 1)
        current_row += 1

        # collect buttons
        darkSpectrum = qt.QPushButton('Collect Dark Spectrum')
        self.spectro['darkSpectrum'] = darkSpectrum
        optGrid.addWidget(darkSpectrum, current_row, 0, 1, 2)
        
        scaleFactor = qt.QPushButton('Calculate Scale Factor')
        scaleFactor.setDisabled(True)
        self.spectro['scaleFactor'] = scaleFactor
        optGrid.addWidget(scaleFactor, current_row, 2, 1, 2)

        current_row += 1

        # progress bars
        darkProgress = qt.QProgressBar()
        darkProgress.setTextVisible(False)
        self.spectro['darkProgress'] = darkProgress
        optGrid.addWidget(darkProgress, current_row, 0, 1, 2)

        scaleProgress = qt.QProgressBar()
        scaleProgress.setTextVisible(False)
        self.spectro['scaleProgress'] = scaleProgress
        optGrid.addWidget(scaleProgress, current_row, 2, 1, 2)

        self.spectroLayout.addWidget(optPane)
        self.spectroLayout.addStretch()

        self.layout.addWidget(self.spectroPane, *pos)
    
    def chooseDirectory(self):
        saveDir = qt.QFileDialog.getExistingDirectory(self.mainWindow.measureTab, 'Choose Save Directory', self.program.config.get('saveDir'), qt.QFileDialog.ShowDirsOnly)
        if saveDir != '':
            self.program.updateConfig('saveDir', saveDir)
        self.saveDirLabel.setText(self.program.config.get('saveDir'))

    def filePaths(self, *pos):
        self.pathPane = qt.QWidget()
        self.pathLayout = qt.QVBoxLayout(self.pathPane)

        self.pathLayout.addWidget(qt.QLabel("Save Directory", objectName="title"))
        self.pathLayout.addWidget(Hline())

        optPane = qt.QWidget()
        optGrid = qt.QGridLayout(optPane)

        getDirectory = qt.QPushButton("Save in...")
        getDirectory.clicked.connect(self.chooseDirectory)
        optGrid.addWidget(getDirectory, 0, 0, 1, 1)

        self.saveDirLabel = qt.QLineEdit(self.program.config.get('saveDir'))
        optGrid.addWidget(self.saveDirLabel, 0, 1, 1, 3)

        self.pathLayout.addWidget(optPane)
        self.pathLayout.addStretch()
        self.layout.addWidget(self.pathPane, *pos)

    def temperature(self, *pos):

        self.tempPane = qt.QWidget()
        self.tempLayout = qt.QVBoxLayout(self.tempPane)

        self.tempLayout.addWidget(qt.QLabel("Temperature", objectName="title"))
        self.tempLayout.addWidget(Hline())
        
        optPane = qt.QWidget()
        optGrid = qt.QGridLayout(optPane)

        commLink = qt.QComboBox()
        commLink.addItem('Temp 1')
        commLink.addItem('Temp 2')
        self.temp['commLink'] = commLink
        optGrid.addWidget(qt.QLabel('Comm Port:'), 0, 0, alignment=QtCore.Qt.AlignRight)
        optGrid.addWidget(commLink, 0, 1)
        
        thermoType = qt.QComboBox()
        thermoType.addItem('K')
        thermoType.addItem('J')
        thermoType.addItem('T')
        thermoType.addItem('E')
        self.temp['thermoType'] = thermoType
        optGrid.addWidget(qt.QLabel('Thermocouple Type:'), 0, 2, alignment=QtCore.Qt.AlignRight)
        optGrid.addWidget(thermoType, 0, 3)

        self.statusTemp = LEDIndicator()
        optGrid.addWidget(self.statusTemp, 0, 4)

        
        temp_c = qt.QLineEdit(self.program.config.get('temp_c'))
        temp_c.setValidator(qg.QDoubleValidator())
        self.temp['temp_c'] = temp_c
        optGrid.addWidget(qt.QLabel('Temp Offset:'), 1, 0, alignment=QtCore.Qt.AlignRight)
        optGrid.addWidget(temp_c, 1, 1)

        temp_m = qt.QLineEdit(self.program.config.get('temp_m'))
        temp_m.setValidator(qg.QDoubleValidator())
        self.temp['temp_m'] = temp_m
        optGrid.addWidget(qt.QLabel('Temp Slope:'), 1, 2, alignment=QtCore.Qt.AlignRight)
        optGrid.addWidget(temp_m, 1, 3)

        self.tempLayout.addWidget(optPane)

        # # temperature graph
        # graphTempButton = qt.QPushButton("Live Temperature")
        # self.tempLayout.addWidget(graphTempButton)

        # graphTemp = GraphWidget(self)
        # self.graphs['temp'] = graphTemp
        # self.tempLayout.addWidget(graphTemp)

        self.tempLayout.addStretch()

        self.layout.addWidget(self.tempPane, *pos)

    def setupGraphs(self, *pos):
        self.graphPane = qt.QWidget()
        self.graphLayout = qt.QVBoxLayout(self.graphPane)

        graphLayout = pg.GraphicsLayoutWidget()
        graphLayout.setBackground(None)
        self.graphLayout.addWidget(graphLayout)

        # dark spectrum
        self.graphDark = GraphItem()
        graphLayout.addItem(self.graphDark, 0, 0)
        self.graphDark.setLabel('left', 'Intensity')
        # raw intensities
        self.graphChannels = GraphItem(2) 
        graphLayout.addItem(self.graphChannels, 1, 0)
        self.graphChannels.setLabel('left', 'Intensity')
        # scale factor
        self.graphScale = GraphItem()
        graphLayout.addItem(self.graphScale, 2, 0)
        self.graphScale.setLabel('left', 'Scale Factor')
        self.graphScale.setLabel('bottom', 'Wavelength')

        # link X axes
        self.graphChannels.setXLink(self.graphDark)
        self.graphScale.setXLink(self.graphDark)

        self.layout.addWidget(self.graphPane, *pos)

    def connections(self):
        # spectrometer connection
        self.spectro['specConnectButton'].clicked.connect(self.program.connectSpectrometer)
        self.spectro['specRefreshButton'].clicked.connect(self.refreshSpectrometers)
        self.spectro['commLink'].currentIndexChanged.connect(self.program.change_spectrometer)
        
        
        # change integration time or nscans
        self.spectro['integrationTime'].textChanged.connect(partial(self.program.update_parameter, 'spectro', 'integrationTime', int))
        self.spectro['nScans'].textChanged.connect(partial(self.program.update_parameter, 'spectro', 'nScans', int))

        # change wavelength limits
        self.spectro['wvMin'].textChanged.connect(partial(self.program.update_parameter, 'spectro', 'wvMin', int))
        self.spectro['wvMax'].textChanged.connect(partial(self.program.update_parameter, 'spectro', 'wvMax', int))

        # temp calibration changed
        self.temp['temp_c'].textChanged.connect(partial(self.program.update_parameter, 'temp', 'temp_c', float))
        self.temp['temp_m'].textChanged.connect(partial(self.program.update_parameter, 'temp', 'temp_m', float))

        # measure and display dark spectrum
        self.spectro['darkSpectrum'].clicked.connect(partial(self.program.collectDark, self.graphDark.lines[0], 'incremental'))

        # measure and display scale factor
        self.spectro['scaleFactor'].clicked.connect(partial(self.program.collectScaleFactor, self.graphChannels.lines, 'incremental'))
