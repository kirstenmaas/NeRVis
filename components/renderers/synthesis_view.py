import numpy as np

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
    def __init__(self, frame, data):
        self.frame = frame

        self.data = data
        self.drawn_angles = data.drawn_angles
        self.images_path = f'{data.data_path}/precomputed_views/'

        self.setup_image_layout(f"{self.images_path}/0313.png")

    def setup_image_layout(self, image_path="0001.png"):
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

    def show_image_by_angle(self, azimuth, elevation):
        closest_angle_index = self.find_closest_drawn_angle(azimuth, elevation)
        image_file_name = str(int(closest_angle_index)).zfill(4) + '.png'
        image_path = self.images_path + image_file_name
        self.update_image(image_path)

    def update_image(self, image_path="0001.png"):
        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(self.width, self.height)
        self.label.setPixmap(pixmap)

    def find_closest_drawn_angle(self, azimuth, elevation):
        min_distance = np.inf
        closest_angle = None
        closest_angle_index = -1

        for index, row in self.data.drawn_angles.iterrows():
            drawn_azimuth = row['azimuth']
            drawn_elevation = row['elevation']

            distance = np.sqrt((azimuth - drawn_azimuth)**2 + (elevation - drawn_elevation)**2)

            if distance < min_distance:
                min_distance = distance
                closest_angle = (drawn_azimuth, drawn_elevation)
                closest_angle_index = index
        
        return closest_angle_index