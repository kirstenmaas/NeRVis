from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout
)

from PyQt6.QtGui import (
    QPixmap,
)

class SynthesisView():
    def __init__(self, frame):
        self.frame = frame

        self.setup_image()
    
    def setup_image(self):
        frame = self.frame

        layout = QVBoxLayout(frame)
        label = QLabel(frame)
        pixmap = QPixmap("text_render_image.png")

        frame_geom = frame.frameRect()
        width = frame_geom.width()
        height = frame_geom.height()
        pixmap = pixmap.scaled(width, height)
        
        label.setPixmap(pixmap)
        layout.addWidget(label)

        frame.setLayout(layout)