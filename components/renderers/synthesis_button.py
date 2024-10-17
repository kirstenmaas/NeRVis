from PyQt6.QtWidgets import (
    QPushButton,
)

import numpy as np
import pdb
import eval_nerf
import matplotlib.pyplot as plt

class SynthesisButton(QPushButton):
    def __init__(self, text, parent, camera, synthesis_view, data):
        super(QPushButton, self).__init__(text)

        self.setStyleSheet("QPushButton { font-family: Inter; }")

        self.text = text
        self.parent = parent
        self.camera = camera
        self.synthesis_view = synthesis_view
        self.data = data

        parent.addWidget(self)

        self.clicked.connect(self.eval_nerf)

    def eval_nerf(self):
        self.setText('Rendering...')

        camera = self.camera
        synthesis_view = self.synthesis_view
        
        # set the file loaded to "rendering" image
        save_file_name="0001.png"
        synthesis_view.update_image(save_file_name)

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

        original_distance = 5
        focal_length = original_distance / camera.GetDistance() * (1200)

        eval_nerf.get_render_image(vector_magnitude, rotation_matrix, focal_length, self.data, save_file_name)

        # display the rendered image in the application's frame
        synthesis_view.update_image(save_file_name)

        self.setText(self.text)

