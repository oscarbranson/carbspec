# Modified from: https://github.com/nlamprian/pyqt5-led-indicator-widget/blob/master/LedIndicatorWidget.py

from PyQt5.QtCore import QPointF, pyqtProperty
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush
from PyQt5.QtWidgets import QAbstractButton


class LEDIndicator(QAbstractButton):
    scaledSize = 1000.0

    def __init__(self, parent=None):
        super().__init__()

        self.setMinimumSize(15, 15)
        self.setCheckable(True)

        self.on_color = QColor(95, 142, 185)
        self.off_color = QColor(220, 230, 239)
        self.edge_color = QColor(62, 103, 142)

    def resizeEvent(self, QResizeEvent):
        self.update()

    def mousePressEvent(self, QMouseEvent):
        # don't respond to mouse clicks
        return

    def paintEvent(self, QPaintEvent):
        realSize = min(self.width(), self.height())

        # set up painter
        painter = QPainter(self)
        pen = QPen(self.edge_color)
        pen.setWidth(1)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(realSize / self.scaledSize, realSize / self.scaledSize)

        # draw background
        painter.setPen(pen)
        painter.setBrush(QBrush(self.edge_color))
        painter.drawEllipse(QPointF(0, 0), 500, 500)

        # draw fill colour
        painter.setPen(pen)
        if self.isChecked():
            painter.setBrush(self.on_color)
        else:
            painter.setBrush(self.off_color)
        painter.drawEllipse(QPointF(0, 0), 450, 450)

    @pyqtProperty(QColor)
    def onColor(self):
        return self.on_color

    @onColor.setter
    def onColor(self, color):
        self.on_color = color

    @pyqtProperty(QColor)
    def edgeColor(self):
        return self.edge_color

    @edgeColor.setter
    def edgeColor(self, color):
        self.edge_color = color
    
    @pyqtProperty(QColor)
    def offColor(self):
        return self.off_color

    @offColor.setter
    def offColor(self, color):
        self.off_color = color
    
    def setSize(self, size):
        self.setMinimumSize(size, size)

