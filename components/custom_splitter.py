from PyQt6.QtWidgets import (
    QSplitter,
)

from PyQt6.QtCore import (
    Qt,
)

class CustomSplitter(QSplitter):
    def __init__(self, style_sheet=None, orientation='horizontal'):
        orientation_class = self.getOrientation(orientation)

        super(QSplitter, self).__init__(orientation_class)

        if style_sheet:
            self.setStyleSheet(style_sheet)

    def getOrientation(self, orientation):
        orientation_class = Qt.Orientation.Horizontal
        if orientation == 'vertical':
            orientation_class = Qt.Orientation.Vertical
        return orientation_class

    def addWidgets(self, widgets, stretch_factors):
        for widget in widgets:
            self.addWidget(widget)
        self.setStretchFactors(stretch_factors)

    def setStretchFactors(self, stretch_factors):
        for stretch_factor in stretch_factors:
            self.setStretchFactor(stretch_factor[0], stretch_factor[1])