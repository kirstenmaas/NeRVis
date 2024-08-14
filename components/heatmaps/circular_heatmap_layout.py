from PyQt6.QtWidgets import QHBoxLayout
from .circular_heatmap_view import CircularHeatmapView

import numpy as np

class CircularHeatmapLayout(QHBoxLayout):
    def __init__(self, parent, title, value_data, std_data, training_angles, camera, is_top=True):
        super().__init__(parent)

        parent_size = parent.geometry().width()

        self.setContentsMargins(0,0,0,0)

        self.heatmap_view = CircularHeatmapView(title, value_data, std_data, training_angles, parent_size, camera, is_top=is_top)
        self.addWidget(self.heatmap_view)

    def set_other_heatmap_layouts(self, other_heatmap_layouts):
        self.heatmap_view.set_other_heatmap_layouts(other_heatmap_layouts)