from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

import pyqtgraph as pg

colour_main = (95, 142, 185)
colour_light = (184, 205, 224)
colour_lighter = (220, 230, 239)
colour_dark = (62, 103, 142)
colour_darker = (31, 52, 71)

colour_acid = colour_dark
colour_base = (142, 101, 62)

colour_main_str = "rgb({}, {}, {})".format(*colour_main)
colour_light_str = "rgb({}, {}, {})".format(*colour_light)
colour_lighter_str = "rgb({}, {}, {})".format(*colour_lighter)
colour_dark_str = "rgb({}, {}, {})".format(*colour_dark)
colour_darker_str = "rgb({}, {}, {})".format(*colour_darker)

# text styles
title = 'font: bold 12pt; color: rgb({}, {}, {})'.format(*colour_dark)
label = "font: bold 10pt; color: rgb({}, {}, {})".format(*colour_darker)
choice = "font: 10pt; color: rgb({}, {}, {})".format(*colour_dark)

stylelist = [
    "QTabBar::tab:selected {background:" + colour_main_str + "; font: bold 12pt; color: " + colour_darker_str + ";}",
    "QTabBar::tab {background: " + colour_light_str + "; font: bold 12pt; color: " + colour_darker_str + "; width: 200px;}",
    # "QPushButton {font: bold 10pt; color: " + colour_darker_str + "; background-color: " + colour_main_str + "; border: none;}"
    # "QPushButton:disabled {font: bold 10pt; color: " + colour_main_str + "}"
    "QPushButton {border: 0px solid red; border-radius: 3px; background-color: blue}",
    "QPushButton#pushButton:disabled {border: 2px solid blue;}",
    ]
# styleSheet = '\n'.join(stylelist)
styleSheet = """
QTabBar::tab {font: bold 12pt; width: 200px;}
"""

# graphs
graphPen = pg.mkPen(colour_darker, width=2)
graphBkg = None


# # palette
# palette = QPalette()
# # palette.setColor(QPalette.Window, Qt.white)
# # palette.setColor(QPalette.WindowText, QColor(*colour_darker))
# # palette.setColor(QPalette.Button, Qt.red)
# # palette.setColor(QPalette.ButtonText, Qt.black)