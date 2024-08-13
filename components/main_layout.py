from PyQt6.QtWidgets import (
    QHBoxLayout,
)

from .styles import frame_style, border_style

from .custom_frame import CustomFrame
from .custom_layout import CustomQHLayout, CustomQVLayout, CustomGridLayout
from .custom_tab_widget import CustomTabWidget
from .custom_splitter import CustomSplitter

class MainLayout(QHBoxLayout):
    def __init__(self, parent):
        super(QHBoxLayout, self).__init__(parent)

        self.main_setup()

    def main_setup(self):
        self.info_setup()
        self.renderer_setup()
        self.vis_setup()
        self.splitter_setup()

    def info_setup(self):
        self.info_frame = CustomFrame(name='info_frame', style_sheet=border_style)
        self.info_layout = CustomQVLayout(parent=self.info_frame, name='info_layout')
    
    def renderer_setup(self):
        self.renderers_frame = CustomFrame(name='renderers_frame', style_sheet=border_style)
        self.renderers_layout = CustomGridLayout(parent=self.renderers_frame, name='renderers_layout')

        self.synthesis_frame = CustomFrame(name='synthesis_frame', style_sheet=frame_style, width=500, height=500)
        self.uncertainty_vol_frame = CustomFrame(name='uncertainty_vol_frame', style_sheet=frame_style, width=500, height=500)
        self.isosurface_frame = CustomFrame(name='isosurface_frame', style_sheet=frame_style, width=500, height=500)
        self.empty_renderer_frame = CustomFrame(name='empty_frame', style_sheet=frame_style, width=500, height=500)

        renderers_frames = [[self.synthesis_frame, self.uncertainty_vol_frame], [self.isosurface_frame, self.empty_renderer_frame]]
        self.renderers_layout.addWidgets(renderers_frames)
    
    def vis_setup(self):
        self.vis_frame = CustomFrame(name='vis_frame', style_sheet=border_style)
        self.vis_layout = CustomQHLayout(parent=self.vis_frame, name='vis_layout')

        self.vis_tab_widget = CustomTabWidget(name='vis_tabs')
        self.vis_layout.addWidget(self.vis_tab_widget)

    def splitter_setup(self):
        self.splitter = CustomSplitter()
        self.splitter.addWidgets([self.info_frame, self.renderers_frame, self.vis_frame], [[0,1], [1,1], [2,1]])
        self.addWidget(self.splitter)

