from PyQt6.QtWidgets import (
    QTabWidget,
    QWidget,
    QGridLayout,
    QVBoxLayout
)

from .custom_frame import CustomFrame
from .styles import frame_style_sheet

class CustomTabWidget(QTabWidget):
    def __init__(self, name):
        super(QTabWidget, self).__init__()

        self.name = name
        self.setStyleSheet(frame_style_sheet)

        self.create_tabs()
        self.setup_tf_tab()
        self.setup_heatmap_tab()
    
    def create_tabs(self):
        self.tf_tab = QWidget()
        self.heatmap_tab = QWidget()
        
        self.addTab(self.tf_tab, "Transfer functions")
        self.addTab(self.heatmap_tab, "Heatmaps")

    def setup_tf_tab(self):
        tf_tab = self.tf_tab

        self.tf_layout = QGridLayout(tf_tab)
        self.tf_tf_frame = CustomFrame(name='tf_frame', style_sheet=frame_style_sheet, width=500, height=500)
        
        self.setup_scalar_tf()

        self.tf_distr_frame = CustomFrame(name='distr_frame', style_sheet=frame_style_sheet, width=1000, height=500)

        self.tf_layout.addWidget(self.tf_tf_frame, 0, 0)
        self.tf_layout.addWidget(self.tf_scalar_widget, 0, 1)
        self.tf_layout.addWidget(self.tf_distr_frame, 1, 0, 1, 2)

    def setup_heatmap_tab(self):
        heatmap_tab = self.heatmap_tab

        self.heatmap_layout = QGridLayout(heatmap_tab)
        self.mean_heatmap_frame = CustomFrame(name='mean_heatmap_frame', style_sheet=frame_style_sheet, width=500, height=500)
        self.std_heatmap_frame = CustomFrame(name='std_heatmap_frame', style_sheet=frame_style_sheet, width=500, height=500)
        self.empty_frame_1 = CustomFrame(name='empty_frame_1', style_sheet=frame_style_sheet, width=500, height=500)
        self.empty_frame_2 = CustomFrame(name='empty_frame_2', style_sheet=frame_style_sheet, width=500, height=500)

        self.heatmap_layout.addWidget(self.mean_heatmap_frame, 0, 0)
        self.heatmap_layout.addWidget(self.std_heatmap_frame, 0, 1)
        self.heatmap_layout.addWidget(self.empty_frame_1, 1, 0)
        self.heatmap_layout.addWidget(self.empty_frame_2, 1, 1)
    
    def setup_scalar_tf(self):
        self.tf_scalar_widget = QWidget()

        self.tf_scalar_layout = QVBoxLayout()
        self.tf_scalar_graph_frame = CustomFrame(name='scalar_graph_frame', style_sheet=frame_style_sheet, width=500, height=460)
        self.tf_scalar_control_frame = CustomFrame(name='scalar_control_frame', style_sheet=frame_style_sheet, width=500, height=40)

        self.tf_scalar_layout.addWidget(self.tf_scalar_graph_frame)
        self.tf_scalar_layout.addWidget(self.tf_scalar_control_frame)
        self.tf_scalar_widget.setLayout(self.tf_scalar_layout)