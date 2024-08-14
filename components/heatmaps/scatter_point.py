from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtGui import QTransform, QColor

class ScatterPoint(QGraphicsEllipseItem):
    def __init__(self, x, y, diameter=10):
        super(QGraphicsEllipseItem, self).__init__(x, y, diameter, diameter)

        self.diameter = diameter
        self.is_parent_pie = False
        self.parent_pie = None
    
        self.translate()
        self.set_color()

    def translate(self):
        transform = QTransform()
        transform.translate(-self.diameter/2, -self.diameter/2)
        self.setTransform(transform)
    
    def set_color(self, color=[0, 0, 255, 1]):
        brush = QColor(color[0], color[1], color[2], color[3])
        self.setBrush(brush)
        # self.setPen(None)

    def set_parent_pie(self, pie):
        self.parent_pie = pie