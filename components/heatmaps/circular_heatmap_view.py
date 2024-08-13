from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtGui import QTransform

from .circular_heatmap_scene import CircularHeatmapScene

class CircularHeatmapView(QGraphicsView):
    def __init__(self, value_data, training_angles, outer_diameter=500, camera=None):
        super(CircularHeatmapView, self).__init__()

        self.disableMove = False

        self.setMinimumSize(outer_diameter, outer_diameter)
        self.setMaximumSize(outer_diameter, outer_diameter)

        self.setMouseTracking(True)

        self.heatmap_scene = CircularHeatmapScene(value_data, training_angles, outer_diameter=outer_diameter-10)
        self.setScene(self.heatmap_scene)

        self.camera = camera
    
    def mouseMoveEvent(self, event):
        pass
        pie = self.getPieAtLoc(event)
        if pie and not self.disableMove:
            self.camera.update_angles(pie.theta, pie.phi)

    def mousePressEvent(self, event, selected_pen_width=3):
        current_pie = self.getPieAtLoc(event)

        if current_pie:
            print(current_pie.theta, current_pie.phi)
            if current_pie.pen_width == selected_pen_width:
                current_pie.set_pen()
                self.disableMove = False
            else:
                for pie in self.heatmap_scene.pies:
                    pie.set_pen()

                self.camera.update_angles(current_pie.theta, current_pie.phi)
                current_pie.set_pen(width=selected_pen_width)
                self.disableMove = True
        else:
            self.disableMove = False
    
    def getPieAtLoc(self, event):
        scene = self.scene()
        transform = QTransform()

        translate = scene.outer_diameter/2

        x_pos = event.pos().x() - translate
        y_pos = event.pos().y() - translate
        
        item = scene.itemAt(x_pos, y_pos, transform)
        if not item:
            return None
        
        return item if item.is_pie else None

