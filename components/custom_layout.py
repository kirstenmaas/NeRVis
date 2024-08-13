from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout
)

class CustomQVLayout(QVBoxLayout):
    def __init__(self, parent, name, splitter=None):
        super(QVBoxLayout, self).__init__(parent)

        self.name = name

        if splitter:
            self.addWidget(splitter)

class CustomQHLayout(QHBoxLayout):
    def __init__(self, parent, name, splitter=None):
        super(QHBoxLayout, self).__init__(parent)

        self.name = name

        if splitter:
            self.addWidget(splitter)

class CustomGridLayout(QGridLayout):
    def __init__(self, parent, name):
        super(QGridLayout, self).__init__(parent)

        self.name = name

    def addWidgets(self, grid_frames):
        for i, row in enumerate(grid_frames):
            for j, frame in enumerate(grid_frames[i]):
                self.addWidget(frame, i, j)