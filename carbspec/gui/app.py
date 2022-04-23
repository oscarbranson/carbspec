import PyQt5.QtWidgets as qt
from PyQt5 import QtCore, QtGui
import sys

from program import Program
from setupPane import setupPane
from measurePane import measurePane
import styles
from pkg_resources import resource_filename

class MainWindow(qt.QMainWindow):
    """
    The main GUI window. All of the GUI functionality is built through this class.
    """

    def __init__(self):
        """ The initialisation method creates the window and then runs the UI initialisation. """

        super().__init__()
        
        self.setWindowTitle("carbspec")
        
        # Determines where the offset for where the window appears on the screen.
        # Moves the window x pixels to the right, and y pixels down
        self.screenSize = qt.QDesktopWidget().screenGeometry ( -1 )
        self.resize (self.screenSize.width(), self.screenSize.height())

        # running program object
        self.program = Program(self)

        # We move on to build the UI
        self.initUI()

        self.set_styleSheet()
    
    def initUI(self):

        self.mainWidget = qt.QWidget()
        self.setCentralWidget(self.mainWidget)
        self.mainLayout = qt.QVBoxLayout(self.mainWidget)

        # The file menu is produced here
        # self.initFileMenu()

        # create tabs widget
        self.tabs = qt.QTabWidget()
        self.mainLayout.addWidget(self.tabs)

        # Setup collection tab
        self.setupTab = qt.QWidget(objectName='tabcontents')
        # self.setupTab.setPalette(self.palette)
        self.setupPane = setupPane(self)
        self.tabs.addTab(self.setupTab, 'Setup')
        
        # data collection tab
        self.measureTab = qt.QWidget(objectName='tabcontents')
        # self.measureTab.setPalette(self.palette)
        self.measurePane = measurePane(self)
        self.tabs.addTab(self.measureTab, 'Measure')

        reloadStyle = qt.QPushButton('Reload Stylesheet')
        self.mainLayout.addWidget(reloadStyle)
        reloadStyle.setShortcut('Shift+Ctrl+R')
        reloadStyle.clicked.connect(self.set_styleSheet)
        
        # keyboard shortcuts
        qt.QShortcut(QtGui.QKeySequence('Ctrl+Q'), self, self.exit)

        # # settings tab
        # self.optionsTab = qt.QWidget()
        # self.optionsTab.layout = qt.QVBoxLayout()
        # self.optionsTab.setLayout(self.optionsTab.layout)
        # self.tabs.addTab(self.optionsTab, 'Options')
    
    def set_styleSheet(self):
        with open(resource_filename('carbspec', 'gui/stylesheet.qss'), 'r') as f:
            styleSheet = f.read()
        self.setStyleSheet(styleSheet)
    
    def closeEvent(self, event):
        self.program.writeConfig()

        if self.program.spectrometer is not None:
            msg = f'  -> Disconnected from {self.program.spectrometer.serial_number}'
            self.program.spectrometer.close()
            print(msg)
        event.accept()

    def exit(self):
        app.exit()

if __name__ == '__main__':
    app = qt.QApplication(sys.argv)
    
    app.setStyle('Fusion')

    # palette = app.palette()
    # palette.setColor(QtGui.QPalette.Text, QtGui.QColor(*styles.colour_darker))
    # palette.setColor(QtGui.QPalette.Button, QtGui.QColor(*styles.colour_lighter))

    # app.setPalette(palette)

    # app.setStyleSheet(styles.styleSheet)
    
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
