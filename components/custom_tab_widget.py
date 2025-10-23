from PyQt6.QtWidgets import (
    QTabWidget,
    QWidget,
    QGridLayout,
    QVBoxLayout
)

from PyQt6.QtCore import Qt

from .custom_frame import CustomFrame
from .styles import frame_style_sheet, frame_style_sheet_border

class CustomTabWidget(QTabWidget):
    def __init__(self, name, window_size):
        super(QTabWidget, self).__init__()

        self.window_size = window_size

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
        self.tf_density_frame = CustomFrame(name='tf_density_frame', style_sheet=frame_style_sheet, width=self.window_size, height=self.window_size)
        
        self.setup_scalar_tf()

        self.tf_color_frame = CustomFrame(name='tf_color_frame', style_sheet=frame_style_sheet, width=self.window_size, height=self.window_size)
        self.tf_distr_frame = CustomFrame(name='distr_frame', style_sheet=frame_style_sheet, width=self.window_size, height=self.window_size)

        self.tf_layout.addWidget(self.tf_density_frame, 0, 0)
        self.tf_layout.addWidget(self.tf_distr_frame, 0, 1)
        self.tf_layout.addWidget(self.tf_color_frame, 1, 0)
        self.tf_layout.addWidget(self.tf_scalar_widget, 1, 1)

    def setup_heatmap_tab(self):
        heatmap_tab = self.heatmap_tab

        self.heatmap_layout = QGridLayout(heatmap_tab)
        self.heatmap_layout.setVerticalSpacing(25)
        
        self.mean_heatmap_frame_top = CustomFrame(name='mean_heatmap_frame_top', style_sheet=frame_style_sheet, width=self.window_size, height=self.window_size)
        self.mean_heatmap_frame_bottom = CustomFrame(name='mean_heatmap_frame_bottom', style_sheet=frame_style_sheet, width=self.window_size, height=self.window_size)
        self.mean_color_heatmap_frame_top = CustomFrame(name='mean_color_heatmap_frame_top', style_sheet=frame_style_sheet, width=self.window_size, height=self.window_size)
        self.mean_color_heatmap_frame_bottom = CustomFrame(name='mean_color_heatmap_frame_bottom', style_sheet=frame_style_sheet, width=self.window_size, height=self.window_size)

        self.mean_heatmap_colorbar = CustomFrame(name='mean_heatmap_colorbar', style_sheet=frame_style_sheet, width=int(self.window_size/4), height=self.window_size)
        self.mean_color_heatmap_colorbar = CustomFrame(name='mean_color_heatmap_colorbar', style_sheet=frame_style_sheet, width=int(self.window_size/4), height=self.window_size)

        self.heatmap_legend = CustomFrame(name='heatmap_legend', style_sheet=frame_style_sheet, width=int(self.window_size*2+self.window_size/4), height=int(self.window_size/8))
        self.radio_button_frame = CustomFrame(name='radio_button_frame', style_sheet=frame_style_sheet, width=int(self.window_size*2+self.window_size/4), height=int(self.window_size/8))

        self.heatmap_layout.addWidget(self.mean_heatmap_frame_top, 0, 0)
        self.heatmap_layout.addWidget(self.mean_heatmap_frame_bottom, 0, 1)
        self.heatmap_layout.addWidget(self.mean_heatmap_colorbar, 0, 2)
        
        self.heatmap_layout.addWidget(self.mean_color_heatmap_frame_top, 1, 0)
        self.heatmap_layout.addWidget(self.mean_color_heatmap_frame_bottom, 1, 1)
        self.heatmap_layout.addWidget(self.mean_color_heatmap_colorbar, 1, 2)
        self.heatmap_layout.addWidget(self.heatmap_legend, 2, 0, 1, -1)
        self.heatmap_layout.addWidget(self.radio_button_frame, 3, 0, 1, -1)
    
    def setup_scalar_tf(self):
        self.tf_scalar_widget = QWidget()

        # self.tf_scalar_layout = QVBoxLayout()
        # self.tf_scalar_layout.setContentsMargins(0, 0, 0, 0)
        # self.tf_scalar_layout.setSpacing(0)

        # self.tf_scalar_graph_frame = CustomFrame(name='scalar_graph_frame', style_sheet=frame_style_sheet, width=self.window_size, height=self.window_size-40)
        # self.tf_scalar_control_frame = CustomFrame(name='scalar_control_frame', style_sheet=frame_style_sheet, width=self.window_size, height=40)

        # self.tf_scalar_layout.addWidget(self.tf_scalar_graph_frame)
        # self.tf_scalar_layout.addWidget(self.tf_scalar_control_frame)

        # self.tf_scalar_widget.setLayout(self.tf_scalar_layout)