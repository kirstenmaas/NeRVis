from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtGui import QTransform

from .circular_heatmap_scene import CircularHeatmapScene

import numpy as np

class CircularHeatmapView(QGraphicsView):
    def __init__(self, title, value_data, std_data, training_angles, outer_diameter=500, camera=None, is_top=True):
        super(CircularHeatmapView, self).__init__()

        self.selected_pen_width = 4
        self.hover_pen_width = 2
        self.disableMove = False

        self.setMinimumSize(outer_diameter, outer_diameter)
        self.setMaximumSize(outer_diameter, outer_diameter)

        self.setMouseTracking(True)

        self.heatmap_scene = CircularHeatmapScene(title, value_data, std_data, training_angles, outer_diameter=outer_diameter-10, is_top=is_top)
        self.setScene(self.heatmap_scene)

        self.camera = camera
        self.title = title
        self.other_heatmap_layouts = []
    
    def mouseMoveEvent(self, event):
        current_pie = self.getPieAtLoc(event)

        if current_pie and not self.disableMove:
            if current_pie.theta != None and current_pie.phi != None:
                self.camera.update_angles(current_pie.azimuth, current_pie.elevation)

                # reset pen for all pies
                for pie in self.heatmap_scene.pies:
                    pie.set_pen()
                
                # set hover width for current pie
                current_pie.set_pen(self.hover_pen_width)

                # in other layouts for which the orientation is the same (is_top), do the same and find the correct pie
                for other_layout in self.other_heatmap_layouts:
                    other_scene = other_layout.heatmap_view.heatmap_scene

                    index_pie = None
                    for other_pie in other_scene.pies:
                        # reset the pen width
                        other_pie.set_pen()

                        # pie in the same position
                        if other_scene.is_top == self.heatmap_scene.is_top and other_pie.theta == current_pie.theta and other_pie.phi == current_pie.phi:
                            index_pie = other_pie

                    if index_pie:
                        index_pie.set_pen(self.hover_pen_width)

    def mousePressEvent(self, event):
        current_pie = self.getPieAtLoc(event)

        if current_pie:
            if current_pie.pen_width == self.selected_pen_width:
                current_pie.set_pen()
                self.disableMove = False

                for other in self.other_heatmap_layouts:
                    other.heatmap_view.disableMove = False
            else:
                for pie in self.heatmap_scene.pies:
                    pie.set_pen()

                self.camera.update_angles(current_pie.azimuth, current_pie.elevation)
                current_pie.set_pen(width=self.selected_pen_width)
                self.disableMove = True

                for other in self.other_heatmap_layouts:
                    other_heatmap_view = other.heatmap_view
                    other_heatmap_view.disableMove = True

                    for pie in other_heatmap_view.heatmap_scene.pies:
                        pie.set_pen()
        else:
            self.disableMove = False

            for other in self.other_heatmap_layouts:
                other.heatmap_view.disableMove = False
    
    def getPieAtLoc(self, event):
        scene = self.scene()
        transform = QTransform()

        translate = scene.outer_diameter/2

        x_pos = event.pos().x() - translate
        y_pos = event.pos().y() - translate
        
        item = scene.itemAt(x_pos, y_pos, transform)

        if item:
            if item.is_parent_pie:
                return item
            elif item.parent_pie:
                return item.parent_pie
        
        # no item
        return None

    def set_other_heatmap_layouts(self, other_heatmap_layouts):
        self.other_heatmap_layouts = other_heatmap_layouts
