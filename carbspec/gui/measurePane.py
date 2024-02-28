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

    def dataAcquisition(self, *pos):

        self.measPane = qt.QWidget()
        self.measLayout = qt.QVBoxLayout()
        self.measPane.setLayout(self.measLayout)

        label = qt.QLabel("Data Acquisition", objectName="title")
        self.measLayout.addWidget(label)
        self.measLayout.addWidget(Hline())

        filePaths = qt.QWidget()
        fileLayout = qt.QGridLayout(filePaths)

        self.sampleName = qt.QLineEdit('SampleName')
        fileLayout.addWidget(qt.QLabel('Sample Name:'), 1, 0, 1, 1)
        fileLayout.addWidget(self.sampleName, 1, 1, 1, 1)

        self.sampleSalinity = qt.QLineEdit('35')
        self.sampleSalinity.setValidator(qg.QDoubleValidator())
        fileLayout.addWidget(qt.QLabel('Salinity:'), 1, 2, 1, 1)
        fileLayout.addWidget(self.sampleSalinity, 1, 3, 1, 1)

        self.measLayout.addWidget(filePaths)

        self.collectSpectrum = qt.QPushButton('Collect Spectrum')
        self.collectSpectrum.setShortcut('Ctrl+Space')
        self.collectSpectrum.setDisabled(True)
        self.measLayout.addWidget(self.collectSpectrum)
        
        self.collectionPBar = qt.QProgressBar()
        self.collectionPBar.setTextVisible(False)
        self.measLayout.addWidget(self.collectionPBar)
        
        label2 = qt.QLabel("Data Processing", objectName='title')
        self.measLayout.addWidget(label2)
        self.measLayout.addWidget(Hline())

        self.modeTabs = qt.QTabWidget()
        self.measLayout.addWidget(self.modeTabs)

        phPane = qt.QWidget(objectName='tabcontents')
        phLayout = qt.QVBoxLayout(phPane)
        self.modeTabs.addTab(phPane, 'pH (MCP)')
        self.setupPhPane(phLayout)

        alkPane = qt.QWidget(objectName='tabcontents')
        alkLayout = qt.QVBoxLayout(alkPane)
        self.modeTabs.addTab(alkPane, 'Alkalinity (BPB)')
        self.setupAlkPane(alkLayout)

        self.last5Table = qt.QTableWidget()
        self.last5Table.horizontalHeader().setSectionResizeMode(qt.QHeaderView.Stretch)
        self.tableColumns = ['Sample', 'pH', 'Temp', 'Sal']
        self.tableFmts = ['s', '.3f', '.1f', '.1f']
        self.last5Table.setColumnCount(len(self.tableColumns))
        self.last5Table.setHorizontalHeaderLabels(self.tableColumns)
        self.updateTable()

        self.measLayout.addWidget(self.last5Table)

        self.layout.addWidget(self.measPane, *pos)

    def setupPhPane(self, layout):
        self.phControls = {}
        
        # re-fit button
        self.phControls['refit'] = qt.QPushButton('ReFit Data')
        layout.addWidget(self.phControls['refit'])

    def setupAlkPane(self, layout):
        self.alkControls = {}
        
        # re-fit button
        self.alkControls['refit'] = qt.QPushButton('ReFit Data')
        layout.addWidget(self.alkControls['refit'])

    def updateTable(self):
        last5Table = self.program.df.tail(5).loc[:, self.tableColumns]
        self.last5Table.setRowCount(len(last5Table.index))
        self.last5Table.setVerticalHeaderLabels([f'{v:.0f}' for v in last5Table.index[::-1]])
        for i, ind in enumerate(last5Table.index):
            for j, col in enumerate(last5Table.columns):
                self.last5Table.setItem(len(last5Table.index) - i - 1, j, qt.QTableWidgetItem(f'{last5Table.loc[ind,col]:{self.tableFmts[j]}}'))
    
    def setupGraphs(self, *pos):
        self.graphPane = qt.QWidget()
        self.graphLayout = qt.QVBoxLayout(self.graphPane)
        
        graphLayout = pg.GraphicsLayoutWidget()
        graphLayout.setBackground(None)
        self.graphLayout.addWidget(graphLayout)

        # raw data graph
        self.graphRaw = GraphItem(2)
        graphLayout.addItem(self.graphRaw, 0, 0)
        self.graphRaw.setLabel('left', "Intensity")

        # absorption spectrum
        self.graphAbs = GraphItem()
        graphLayout.addItem(self.graphAbs, 1, 0)
        self.graphAbs.setLabel('left', "Absorption")

        # fit residual
        self.graphResid = GraphItem()
        graphLayout.addItem(self.graphResid, 2, 0)
        self.graphResid.setLabel('left', "Residual")
        self.graphResid.setLabel('bottom', "Wavelength")

        graphLayout.ci.layout.setRowStretchFactor(0,1)
        graphLayout.ci.layout.setRowStretchFactor(1, 2)
        graphLayout.ci.layout.setRowStretchFactor(2, 1)

        # link X axes
        self.graphAbs.setXLink(self.graphRaw)
        self.graphResid.setXLink(self.graphRaw)

        # self.graphLayout.addStretch()
        self.layout.addWidget(self.graphPane, *pos)

    def connections(self):
        # measure and display spectrum
        self.collectSpectrum.clicked.connect(partial(self.program.collectSpectrum, self.graphRaw.lines, 'incremental'))
        self.collectSpectrum.clicked.connect(self.updateTable)
        
        # Re-fit data
        self.phControls['refit'].clicked.connect(self.program.refitSpectrum)
        self.phControls['refit'].clicked.connect(self.updateTable)

        self.alkControls['refit'].clicked.connect(self.program.refitSpectrum)
        self.alkControls['refit'].clicked.connect(self.updateTable)

        # Sample name changed
        self.sampleName.textChanged.connect(partial(self.program.update_parameter, 'Sample', 'Sample', str))

        # temp calibration changed
        self.sampleSalinity.textChanged.connect(partial(self.program.update_parameter, 'Sal', 'Sal', float))

        self.modeTabs.currentChanged.connect(self.program.dyeSet)