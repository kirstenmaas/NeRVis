from PyQt6.QtWidgets import (
    QHBoxLayout,
)

from .styles import frame_style, border_style, splitter_style_sheet

from .custom_frame import CustomFrame
from .custom_layout import CustomQHLayout, CustomQVLayout, CustomGridLayout
from .custom_tab_widget import CustomTabWidget
from .custom_splitter import CustomSplitter

class MainLayout(QHBoxLayout):
    def __init__(self, parent):
        super(QHBoxLayout, self).__init__(parent)

        self.window_size = 350
        self.button_height = 40

        self.main_setup()

    def main_setup(self):
        self.renderer_setup()
        self.vis_setup()
        self.splitter_setup()
    
    def renderer_setup(self):
        self.renderers_frame = CustomFrame(name='renderers_frame', style_sheet=border_style)
        self.renderers_layout = CustomGridLayout(parent=self.renderers_frame, name='renderers_layout')

        self.synthesis_frame = CustomFrame(name='synthesis_frame', style_sheet=frame_style, width=self.window_size, height=self.window_size)
        self.synthesis_layout = CustomQVLayout(parent=self.synthesis_frame, name='synthesis_layout')
        self.synthesis_layout.setContentsMargins(20, 0, 20, 0)

        vol_window_height = self.window_size-self.button_height
        
        self.synthesis_image_frame = CustomFrame(name='synthesis_image_frame', style_sheet=frame_style, width=vol_window_height, height=vol_window_height)
        self.synthesis_layout.addWidget(self.synthesis_image_frame)

        self.isosurface_frame = CustomFrame(name='isosurface_frame', style_sheet=frame_style, width=self.window_size, height=self.window_size)
        self.isosurface_layout = CustomQVLayout(parent=self.isosurface_frame, name='isosurface_layout')

        self.isosurface_vol_frame = CustomFrame(name='isosurface_vol_frame', style_sheet=frame_style, width=vol_window_height, height=vol_window_height)
        self.isosurface_control_frame = CustomFrame(name='isosurface_control_frame', style_sheet=frame_style, width=vol_window_height, height=self.button_height)
        self.isosurface_layout.addWidget(self.isosurface_vol_frame)
        self.isosurface_layout.addWidget(self.isosurface_control_frame)

        self.uncertainty_density_frame = CustomFrame(name='uncertainty_density_frame', style_sheet=frame_style, width=self.window_size, height=self.window_size)
        self.uncertainty_density_layout = CustomQVLayout(parent=self.uncertainty_density_frame, name='uncertainty_density_layout')
        self.uncertainty_density_vol_frame = CustomFrame(name='uncertainty_density_vol_frame', style_sheet=frame_style, width=vol_window_height, height=vol_window_height)
        self.uncertainty_density_layout.addWidget(self.uncertainty_density_vol_frame)

        self.uncertainty_color_frame = CustomFrame(name='uncertainty_color_frame', style_sheet=frame_style, width=self.window_size, height=self.window_size)
        self.uncertainty_color_layout = CustomQVLayout(parent=self.uncertainty_color_frame, name='uncertainty_color_layout')
        self.uncertainty_color_vol_frame = CustomFrame(name='uncertainty_color_vol_frame', style_sheet=frame_style, width=vol_window_height, height=vol_window_height)
        self.uncertainty_color_layout.addWidget(self.uncertainty_color_vol_frame)

        renderers_frames = [[self.synthesis_frame, self.uncertainty_density_frame], [self.isosurface_frame, self.uncertainty_color_frame]]
        self.renderers_layout.addWidgets(renderers_frames)
    
    def vis_setup(self):
        self.vis_frame = CustomFrame(name='vis_frame', style_sheet=border_style)
        self.vis_layout = CustomQHLayout(parent=self.vis_frame, name='vis_layout')

        self.vis_tab_widget = CustomTabWidget(name='vis_tabs', window_size=self.window_size)
        self.vis_layout.addWidget(self.vis_tab_widget)

    def splitter_setup(self):
        self.splitter = CustomSplitter(style_sheet=splitter_style_sheet)
        self.splitter.addWidgets([self.renderers_frame, self.vis_frame], [[0,1], [1,1], [2,1]])
        self.addWidget(self.splitter)

