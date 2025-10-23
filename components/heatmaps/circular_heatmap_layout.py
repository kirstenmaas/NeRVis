from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QLabel
from .circular_heatmap_view import CircularHeatmapView

from .styles import title_style

import numpy as np

class CircularHeatmapLayout(QVBoxLayout):
    def __init__(self, parent, title, value_data, std_data, max_data,
                 vmax, vmin_std, vmax_std, vmin_max, vmax_max, heatmap_angles, training_angles, 
                 camera, view_synthesis_view, is_top=True):
        super().__init__(parent)

        parent_size = parent.geometry().width()

        self.setContentsMargins(0, 10, 0, 0)
        self.setSpacing(10)

        self.titleLabel = QLabel(title)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setStyleSheet(title_style)

        self.heatmap_view = CircularHeatmapView(title, value_data, std_data, max_data, vmax, 
                                                vmin_std, vmax_std, vmin_max, vmax_max, heatmap_angles, 
                                                training_angles, parent_size-45, camera, view_synthesis_view, is_top=is_top)
        
        self.addWidget(self.titleLabel)
        self.addWidget(self.heatmap_view)

    def set_other_heatmap_layouts(self, other_heatmap_layouts):
        self.heatmap_view.set_other_heatmap_layouts(other_heatmap_layouts)

    def reset_heatmap(self, projection_type, extreme_type):
        self.heatmap_view.reset_heatmap(projection_type, extreme_type)