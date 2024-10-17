from PyQt6.QtWidgets import (
    QFrame,
)

class CustomFrame(QFrame):
    def __init__(self, name, style_sheet=None, width=None, height=None):
        super().__init__()

        self.name = name

        self.setFrameShape(QFrame.Shape.StyledPanel)
        if style_sheet:
            self.setStyleSheet(style_sheet)
        
        if width:
            self.setFixedWidth(width)

        if height:
            self.setFixedHeight(height)

    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)