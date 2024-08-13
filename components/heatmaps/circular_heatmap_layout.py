from PyQt6.QtWidgets import QHBoxLayout
from .circular_heatmap_view import CircularHeatmapView

class CircularHeatmapLayout(QHBoxLayout):
    def __init__(self, parent, value_data, training_angles, camera):
        super().__init__(parent)

        parent_size = parent.geometry().width()

        self.setContentsMargins(0,0,0,0)
        
        self.heatmap_view = CircularHeatmapView(value_data, training_angles, parent_size, camera)
        self.addWidget(self.heatmap_view)