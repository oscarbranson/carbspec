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

class measurePane:
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow

        self.program = self.mainWindow.program

        self.layout = qt.QGridLayout()
        self.layout.setColumnStretch(0,1)
        self.layout.setColumnStretch(1,1)
        # self.layout.setRowStretch(0,1)
        # self.layout.setRowStretch(1,1)

        self.saveDir = '~/'
        self.mainWindow.measureTab.setLayout(self.layout)

        self.graphs = {}

        self.dataAcquisition(0, 0, 1, 1)
        # self.temperature(1, 0, 1, 1)
        self.setupGraphs(0, 1, 2, 1)
        
        self.connections()

    def chooseDirectory(self):
        self.saveDir = qt.QFileDialog.getExistingDirectory(self.mainWindow.measureTab, 'Choose Save Directory', self.saveDir, qt.QFileDialog.ShowDirsOnly)
        self.saveDirLabel.setText(self.saveDir)

    def dataAcquisition(self, *pos):

        self.measPane = qt.QWidget()
        self.measPane.setStyleSheet("background: " + styles.colour_lighter_str)
        self.measLayout = qt.QVBoxLayout()
        self.measPane.setLayout(self.measLayout)

        label = qt.QLabel("Data Acquisition", styleSheet=styles.title)
        self.measLayout.addWidget(label)
        self.measLayout.addWidget(Hline())

        filePaths = qt.QWidget()
        fileLayout = qt.QGridLayout(filePaths)

        self.sampleName = qt.QLineEdit('SampleName')
        fileLayout.addWidget(qt.QLabel('Sample Name:'), 1, 0, 1, 1)
        fileLayout.addWidget(self.sampleName, 1, 1, 1, 3)

        getDirectory = qt.QPushButton("Save in...")
        getDirectory.clicked.connect(self.chooseDirectory)
        fileLayout.addWidget(getDirectory, 0, 0, 1, 1)

        self.saveDirLabel = qt.QLabel(self.saveDir)
        fileLayout.addWidget(self.saveDirLabel, 0, 1, 1, 3)

        self.measLayout.addWidget(filePaths)

        self.collectSpectrum = qt.QPushButton('Collect Spectrum')
        self.collectSpectrum.setShortcut('Ctrl+Return')
        if not self.program.scaleCollected:
            self.collectSpectrum.setDisabled(True)
        self.measLayout.addWidget(self.collectSpectrum)
        
        label2 = qt.QLabel("Data Processing", styleSheet=styles.title)
        self.measLayout.addWidget(label2)
        self.measLayout.addWidget(Hline())

        self.modeTabs = qt.QTabWidget()
        self.measLayout.addWidget(self.modeTabs)

        phPane = qt.QWidget()
        phLayout = qt.QVBoxLayout(phPane)
        self.modeTabs.addTab(phPane, 'pH (MCP)')

        alkPane = qt.QWidget()
        alkLayout = qt.QVBoxLayout(alkPane)
        self.modeTabs.addTab(alkPane, 'Alkalinity (BPB)')

        self.last5Table = qt.QTableWidget()
        self.last5Table.setRowCount(5)
        self.last5Table.setColumnCount(2)
        self.last5Table.setHorizontalHeaderLabels(['pH', 'Temperature'])
        self.last5Table.setVerticalHeaderLabels(self.program.last5['Sample'])
        for i in range(5):
            self.last5Table.setItem(0, i, qt.QTableWidgetItem(self.program.last5['pH'][i]))
            self.last5Table.setItem(1, i, qt.QTableWidgetItem(self.program.last5['Temp'][i]))

        self.measLayout.addWidget(self.last5Table)

        self.layout.addWidget(self.measPane, *pos)

    def setupGraphs(self, *pos):
        self.graphPane = qt.QWidget()
        self.graphPane.setStyleSheet("background: " + styles.colour_lighter_str)
        self.graphLayout = qt.QVBoxLayout()
        self.graphPane.setLayout(self.graphLayout)
        
        # raw data graph
        graphRaw = GraphWidget(self, 2)
        graphRaw.graph.setLabel('left', "Intensity", styleSheet=styles.label)
        self.graphs['raw'] = graphRaw
        self.graphLayout.addWidget(graphRaw)
        self.graphLayout.setStretch(0, 1)

        # absorption spectrum
        graphAbs = GraphWidget(self)
        graphAbs.graph.setLabel('left', "Absorption", styleSheet=styles.label)
        self.graphs['abs'] = graphAbs
        self.graphLayout.addWidget(graphAbs)
        self.graphLayout.setStretch(1, 2)

        # fit residual
        graphResidual = GraphWidget(self)
        graphResidual.graph.setLabel('left', "Residual", styleSheet=styles.label)
        self.graphs['resid'] = graphResidual
        self.graphLayout.addWidget(graphResidual)
        self.graphLayout.setStretch(2, 1)

        self.graphLayout.addStretch()
        self.layout.addWidget(self.graphPane, *pos)

    def connections(self):
        # measure and display spectrum
        self.collectSpectrum.clicked.connect(partial(self.program.collectSpectrum, self.graphs['raw'].lines, 'incremental'))
