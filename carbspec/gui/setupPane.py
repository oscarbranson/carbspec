import PyQt5.QtWidgets as qt
import PyQt5.QtGui as qg
from PyQt5 import QtCore
import pyqtgraph as pg
import numpy as np
from functools import partial

import styles
from graph import GraphItem

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
        self.layout.setRowStretch(0,1)
        self.layout.setRowStretch(1,1)

        self.mainWindow.setupTab.setLayout(self.layout)

        self.graphs = {}
        self.spectro = {}
        self.temp = {}

        self.spectrometer(0, 0, 1, 1)
        self.temperature(1, 0, 1, 1)
        self.setupGraphs(0, 1, 2, 1)
        
        self.connections()

    def spectrometer(self, *pos):
        
        self.spectroPane = qt.QWidget()
        self.spectroLayout = qt.QVBoxLayout()
        self.spectroPane.setLayout(self.spectroLayout)

        self.spectroLayout.addWidget(qt.QLabel("USB Spectrometer", objectName="title"))
        self.spectroLayout.addWidget(Hline())

        optPane = qt.QWidget()
        optGrid = qt.QGridLayout(optPane)

        commLink = qt.QComboBox()
        commLink.addItem('Spec 1')
        commLink.addItem('Spec 2')
        self.spectro['commLink'] = commLink
        optGrid.addWidget(qt.QLabel('Comm Port:'), 0, 0, 1, 1)
        optGrid.addWidget(commLink, 0, 1, 1, 3)

        integTime = qt.QLineEdit(str(self.program.params['spectro']['integrationTime']))
        integTime.setValidator(qg.QIntValidator())
        self.spectro['integrationTime'] = integTime
        optGrid.addWidget(qt.QLabel('Integration Time (ms):'), 1, 0, 1, 1)
        optGrid.addWidget(integTime, 1, 1, 1, 1)

        nScans = qt.QLineEdit(str(self.program.params['spectro']['nScans']))
        nScans.setValidator(qg.QIntValidator())
        self.spectro['nScans'] = nScans
        optGrid.addWidget(qt.QLabel('Replicate Scans:'), 1, 2, 1, 1)
        optGrid.addWidget(nScans, 1, 3, 1, 1)

        self.spectroLayout.addWidget(optPane)

        specSetupPane = qt.QWidget()
        specSetupGrid = qt.QGridLayout(specSetupPane)

        darkSpectrum = qt.QPushButton('Collect Dark Spectrum')
        self.spectro['darkSpectrum'] = darkSpectrum
        specSetupGrid.addWidget(darkSpectrum, 0, 0)

        darkProgress = qt.QProgressBar()
        darkProgress.setTextVisible(False)
        self.spectro['darkProgress'] = darkProgress
        specSetupGrid.addWidget(darkProgress, 1, 0,)

        scaleFactor = qt.QPushButton('Calculate Scale Factor')
        scaleFactor.setDisabled(True)
        self.spectro['scaleFactor'] = scaleFactor
        specSetupGrid.addWidget(scaleFactor, 0, 1)

        scaleProgress = qt.QProgressBar()
        scaleProgress.setTextVisible(False)
        self.spectro['scaleProgress'] = scaleProgress
        specSetupGrid.addWidget(scaleProgress, 1, 1)

        self.spectroLayout.addWidget(specSetupPane)

        self.spectroLayout.addStretch()

        self.layout.addWidget(self.spectroPane, *pos)

    def temperature(self, *pos):

        self.tempPane = qt.QWidget()
        self.tempLayout = qt.QVBoxLayout()
        self.tempPane.setLayout(self.tempLayout)

        self.tempLayout.addWidget(qt.QLabel("Temperature", objectName="title"))
        self.tempLayout.addWidget(Hline())
        
        optPane = qt.QWidget()
        optGrid = qt.QGridLayout(optPane)

        commLink = qt.QComboBox()
        commLink.addItem('Temp 1')
        commLink.addItem('Temp 2')
        self.temp['commLink'] = commLink
        optGrid.addWidget(qt.QLabel('Comm Port:'), 0, 0)
        optGrid.addWidget(commLink, 0, 1)
        
        thermoType = qt.QComboBox()
        thermoType.addItem('K')
        thermoType.addItem('J')
        thermoType.addItem('T')
        thermoType.addItem('E')
        self.temp['thermoType'] = thermoType
        optGrid.addWidget(qt.QLabel('Thermocouple Type:'), 0, 2)
        optGrid.addWidget(thermoType, 0, 3)
        
        calib_c = qt.QLineEdit(str(self.program.params['temp']['calib_c']))
        calib_c.setValidator(qg.QDoubleValidator())
        self.temp['calib_c'] = calib_c
        optGrid.addWidget(qt.QLabel('Temp Offset:'), 1, 0)
        optGrid.addWidget(calib_c, 1, 1)

        calib_m = qt.QLineEdit(str(self.program.params['temp']['calib_m']))
        calib_m.setValidator(qg.QDoubleValidator())
        self.temp['calib_m'] = calib_m
        optGrid.addWidget(qt.QLabel('Temp Slope:'), 1, 2)
        optGrid.addWidget(calib_m, 1, 3)

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
        # change integration time
        self.spectro['integrationTime'].textChanged.connect(partial(self.program.update_parameter, 'spectro', 'integrationTime', int))
        # change n replicates
        self.spectro['nScans'].textChanged.connect(partial(self.program.update_parameter, 'spectro', 'nScans', int))
        
        # measure and display dark spectrum
        self.spectro['darkSpectrum'].clicked.connect(partial(self.program.collectDark, self.graphDark.lines[0], 'incremental'))

        # measure and display scale factor
        self.spectro['scaleFactor'].clicked.connect(partial(self.program.collectScaleFactor, self.graphChannels.lines, 'incremental'))