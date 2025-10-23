from PyQt6.QtWidgets import (
    QPushButton,
)

import numpy as np
import pdb
import eval_nerf
import matplotlib.pyplot as plt

class SynthesisButton(QPushButton):
    def __init__(self, text, parent=None, camera=None, synthesis_view=None, data=None):
        super(QPushButton, self).__init__(text)

        self.setStyleSheet("QPushButton { font-family: Inter; }")

        self.text = text
        self.parent = parent
        self.camera = camera
        self.synthesis_view = synthesis_view
        self.data = data

        if parent:
            parent.addWidget(self)

        self.clicked.connect(self.update_view_synthesis_view)

    def update_view_synthesis_view(self):
        self.setText('Rendering...')

        camera = self.camera
        synthesis_view = self.synthesis_view
        save_file_name = '0001.png'
        infer_nerf(save_file_name, camera, self.data, original_distance=5.0)
        synthesis_view.update_image(save_file_name)
        self.setText(self.text)

def infer_nerf(save_file_name, camera, data, original_distance=3.0):
    mvt_matrix = camera.GetModelViewTransformMatrix()

    rotation_matrix = np.eye(4)
    for row in range(3):
        for col in range(3):
            rotation_matrix[row, col] = mvt_matrix.GetElement(row, col)

    # Get the camera position and focal point
    camera_pos = camera.GetPosition()
    focal_point = camera.GetFocalPoint()

    # Calculate the vector between camera and focal point
    vector = np.array([camera_pos[i] - focal_point[i] for i in range(3)])
    vector_magnitude = np.linalg.norm(vector)

    focal_length = original_distance / camera.GetDistance() * (1200)

    eval_nerf.get_render_image(vector_magnitude, rotation_matrix, focal_length, data, save_file_name)

