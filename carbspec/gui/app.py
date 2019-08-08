import PyQt5.QtWidgets as qt
from PyQt5 import QtCore, QtGui
import sys

from program import Program
from setupPane import setupPane
from measurePane import measurePane
import styles

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

        self.palette = self.palette()
        
        # We move on to build the UI
        self.initUI()

    def initUI(self):
        

        self.mainWidget = qt.QWidget()
        self.setCentralWidget(self.mainWidget)

        # running program object
        self.program = Program(self)

        # principalLayout is a vertical box that runs down the entire window
        self.principalLayout = qt.QVBoxLayout(self.mainWidget)

        # The file menu is produced here
        # self.initFileMenu()

        # mainStack moves between views that occupy the entire window
        self.mainStack = qt.QStackedWidget()

        # Add the mainStack to the principalLayout
        self.principalLayout.addWidget(self.mainStack)

        # Layout to hold the tabs
        self.stageTabsWidget = qt.QWidget()
        self.stagesLayout = qt.QVBoxLayout(self.stageTabsWidget)
        self.mainStack.addWidget(self.stageTabsWidget)

        # create tabs widget
        self.tabs = qt.QTabWidget()
        self.stagesLayout.addWidget(self.tabs)

        # Setup collection tab
        self.setupTab = qt.QWidget()
        self.setupPane = setupPane(self)
        self.tabs.addTab(self.setupTab, 'Setup')
        
        # data collection tab
        self.measureTab = qt.QWidget()
        self.measurePane = measurePane(self)
        self.tabs.addTab(self.measureTab, 'Measure')

        # # settings tab
        # self.optionsTab = qt.QWidget()
        # self.optionsTab.layout = qt.QVBoxLayout()
        # self.optionsTab.setLayout(self.optionsTab.layout)
        # self.tabs.addTab(self.optionsTab, 'Options')

if __name__ == '__main__':
    app = qt.QApplication([])
    
    app.setStyle('Fusion')

    palette = app.palette()
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(*styles.colour_darker))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(*styles.colour_lighter))

    app.setPalette(palette)

    app.setStyleSheet(styles.styleSheet)
    
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
