import PyQt5.QtWidgets as qt
import PyQt5.QtGui as qg
from PyQt5 import QtCore
import pyqtgraph as pg
import numpy as np
from functools import partial

import styles
from graph import GraphWidget

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
        self.spectroPane.setStyleSheet("background: " + styles.colour_lighter_str)
        self.spectroLayout = qt.QVBoxLayout()
        self.spectroPane.setLayout(self.spectroLayout)

        label = qt.QLabel("USB Spectrometer", styleSheet=styles.title)
        self.spectroLayout.addWidget(label)
        self.spectroLayout.addWidget(Hline())

        optPane = qt.QWidget()
        optGrid = qt.QGridLayout(optPane)

        commLink = qt.QComboBox()
        commLink.addItem('Spec 1')
        commLink.addItem('Spec 2')
        self.spectro['commLink'] = commLink
        optGrid.addWidget(qt.QLabel('Comm Port:', styleSheet=styles.label), 0, 0, 1, 1)
        optGrid.addWidget(commLink, 0, 1, 1, 3)

        integTime = qt.QLineEdit(str(self.program.params['spectro']['integrationTime']))
        integTime.setValidator(qg.QIntValidator())
        self.spectro['integrationTime'] = integTime
        optGrid.addWidget(qt.QLabel('Integration Time (ms):', styleSheet=styles.label), 1, 0, 1, 1)
        optGrid.addWidget(integTime, 1, 1, 1, 1)

        nScans = qt.QLineEdit(str(self.program.params['spectro']['nScans']))
        nScans.setValidator(qg.QIntValidator())
        self.spectro['nScans'] = nScans
        optGrid.addWidget(qt.QLabel('Replicate Scans:', styleSheet=styles.label), 1, 2, 1, 1)
        optGrid.addWidget(nScans, 1, 3, 1, 1)

        self.spectroLayout.addWidget(optPane)


        specSetupPane = qt.QWidget()
        specSetupGrid = qt.QGridLayout(specSetupPane)

        darkSpectrum = qt.QPushButton('Collect Dark Spectrum')
        self.spectro['darkSpectrum'] = darkSpectrum
        specSetupGrid.addWidget(darkSpectrum, 0, 0, 1, 1)

        darkProgress = qt.QProgressBar()
        self.spectro['darkProgress'] = darkProgress
        specSetupGrid.addWidget(darkProgress, 0, 1, 1, 2)

        scaleFactor = qt.QPushButton('Calculate Scale Factor')
        scaleFactor.setDisabled(True)
        self.spectro['scaleFactor'] = scaleFactor
        specSetupGrid.addWidget(scaleFactor, 1, 0, 1, 1)

        scaleProgress = qt.QProgressBar()
        self.spectro['scaleProgress'] = scaleProgress
        specSetupGrid.addWidget(scaleProgress, 1, 1, 1, 2)

        self.spectroLayout.addWidget(specSetupPane)

        self.spectroLayout.addStretch()

        self.layout.addWidget(self.spectroPane, *pos)

    def temperature(self, *pos):

        self.tempPane = qt.QWidget()
        self.tempPane.setStyleSheet("background: " + styles.colour_lighter_str)
        self.tempLayout = qt.QVBoxLayout()
        self.tempPane.setLayout(self.tempLayout)

        label = qt.QLabel("Temperature", styleSheet=styles.title)
        self.tempLayout.addWidget(label)
        self.tempLayout.addWidget(Hline())
        
        optPane = qt.QWidget()
        optGrid = qt.QGridLayout(optPane)

        commLink = qt.QComboBox()
        commLink.addItem('Temp 1')
        commLink.addItem('Temp 2')
        self.temp['commLink'] = commLink
        optGrid.addWidget(qt.QLabel('Comm Port:', styleSheet=styles.label), 0, 0)
        optGrid.addWidget(commLink, 0, 1)
        
        thermoType = qt.QComboBox()
        thermoType.addItem('K')
        thermoType.addItem('J')
        thermoType.addItem('T')
        thermoType.addItem('E')
        self.temp['thermoType'] = thermoType
        optGrid.addWidget(qt.QLabel('Thermocouple Type:', styleSheet=styles.label), 0, 2)
        optGrid.addWidget(thermoType, 0, 3)
        
        calib_c = qt.QLineEdit(str(self.program.params['temp']['calib_c']))
        calib_c.setValidator(qg.QDoubleValidator())
        self.temp['calib_c'] = calib_c
        optGrid.addWidget(qt.QLabel('Temp Offset:', styleSheet=styles.label), 1, 0)
        optGrid.addWidget(calib_c, 1, 1)

        calib_m = qt.QLineEdit(str(self.program.params['temp']['calib_m']))
        calib_m.setValidator(qg.QDoubleValidator())
        self.temp['calib_m'] = calib_m
        optGrid.addWidget(qt.QLabel('Temp Slope:', styleSheet=styles.label), 1, 2)
        optGrid.addWidget(calib_m, 1, 3)

        self.tempLayout.addWidget(optPane)

        # temperature graph
        graphTempButton = qt.QPushButton("Live Temperature")
        self.tempLayout.addWidget(graphTempButton)

        graphTemp = GraphWidget(self)
        self.graphs['temp'] = graphTemp
        self.tempLayout.addWidget(graphTemp)

        self.tempLayout.addStretch()

        self.layout.addWidget(self.tempPane, *pos)

    def setupGraphs(self, *pos):
        self.graphPane = qt.QWidget()
        self.graphPane.setStyleSheet("background: " + styles.colour_lighter_str)
        self.graphLayout = qt.QVBoxLayout()
        self.graphPane.setLayout(self.graphLayout)
        
        # background graph
        graphDark = GraphWidget(self)
        graphDark.graph.setLabel('left', "Dark Spectrum", styleSheet=styles.label)
        self.graphs['dark'] = graphDark
        self.graphLayout.addWidget(graphDark)
        self.graphLayout.setStretch(0, 1)

        # scale factor graphs (2)
        graphChannels = GraphWidget(self, 2)
        graphChannels.graph.setLabel('left', "Channel Intensity", styleSheet=styles.label)
        self.graphs['channels'] = graphChannels
        self.graphLayout.addWidget(graphChannels)
        self.graphLayout.setStretch(1, 1)

        graphScale = GraphWidget(self)
        graphScale.graph.setLabel('left', "Scale Factor", styleSheet=styles.label)
        self.graphs['scale'] = graphScale
        self.graphLayout.addWidget(graphScale)
        self.graphLayout.setStretch(2, 1)

        self.graphLayout.addStretch()
        self.layout.addWidget(self.graphPane, *pos)

    def connections(self):
        # change integration time
        self.spectro['integrationTime'].textChanged.connect(partial(self.program.update_parameter, 'spectro', 'integrationTime', int))
        # change n replicates
        self.spectro['nScans'].textChanged.connect(partial(self.program.update_parameter, 'spectro', 'nScans', int))
        
        # measure and display dark spectrum
        self.spectro['darkSpectrum'].clicked.connect(partial(self.program.collectDark, self.graphs['dark'].lines[0], 'incremental'))

        # measure and display scale factor
        self.spectro['scaleFactor'].clicked.connect(partial(self.program.collectScaleFactor, self.graphs['channels'].lines, 'incremental'))
