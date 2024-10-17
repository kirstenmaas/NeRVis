from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout
)

from PyQt6.QtGui import (
    QPixmap,
)

title_style = """
    QLabel {
        font-family: Inter;
        font-size: 16px;
        font-weight: 500;
    }
"""

class SynthesisView():
    def __init__(self, frame):
        self.frame = frame

        self.setup_image_layout("0000.png")

    def setup_image_layout(self, image_path="rendering.png"):
        frame = self.frame
        
        self.layout = QVBoxLayout(frame)
        self.label = QLabel(frame)

        self.title = QLabel('View Synthesis')
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(title_style)

        frame_geom = frame.frameRect()
        self.width = frame_geom.width()
        self.height = frame_geom.height()

        self.update_image(image_path)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.label)

        frame.setLayout(self.layout)

    def update_image(self, image_path="rendering.png"):
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(self.width, self.height)
        self.label.setPixmap(pixmap)