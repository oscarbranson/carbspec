import pyqtgraph as pg
import PyQt5.QtWidgets as qt
import styles

# pg.setConfigOptions(antialias=True)
color_order = [styles.colour_darker, styles.colour_main, styles.colour_light]

class GraphWidget(qt.QWidget):

    def __init__(self, parent, nlines=1):
        super().__init__()

        self.parent = parent

        self.layout = qt.QHBoxLayout()
        self.setLayout(self.layout)

        self.view = pg.GraphicsView()
        self.graphLayout = pg.GraphicsLayout()
        self.view.setCentralItem(self.graphLayout)

        self.view.setBackground(None)

        self.graph = pg.PlotItem(background=None)
        self.graphLayout.addItem(self.graph)

        self.lines = {}
        self.pens = {}
        for i in range(nlines):
            self.pens[i] = pg.mkPen(color_order[i], width=2)
            self.lines[i] = pg.PlotDataItem([], [], pen=self.pens[i])
            self.graph.addItem(self.lines[i])

        self.xaxis = self.graph.getAxis('bottom')
        self.yaxis = self.graph.getAxis('left')
        self.xaxis.setPen(styles.graphPen)
        self.yaxis.setPen(styles.graphPen)

        self.layout.addWidget(self.view, 1)

class GraphItem(pg.PlotItem):
    def __init__(self, nlines=1):
        super().__init__()
    
        self.lines = {}
        self.pens = {}
        for i in range(nlines):
            self.pens[i] = pg.mkPen(color_order[i], width=2)
            self.lines[i] = pg.PlotDataItem([], [], pen=self.pens[i])
            self.addItem(self.lines[i])

        self.xaxis = self.getAxis('bottom')
        self.yaxis = self.getAxis('left')
        self.xaxis.setPen(styles.graphPen)
        self.yaxis.setPen(styles.graphPen)