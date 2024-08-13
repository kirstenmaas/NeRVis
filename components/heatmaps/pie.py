from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PyQt6.QtGui import QTransform, QPen, QColor

class Pie(QGraphicsEllipseItem):
    def __init__(self, xy, diameter):
        super(QGraphicsEllipseItem, self).__init__(xy, xy, diameter, diameter)

        self.is_pie = True
        self.diameter = diameter
        self.set_transform()
        self.set_pen()
    
    def set_as_pie(self, start_angle, span_angle):
        self.setStartAngle(start_angle)
        self.setSpanAngle(span_angle)

    def set_color(self, color):
        brush = QColor(color[0], color[1], color[2])
        self.setBrush(brush)

    def set_transform(self):
        transform = QTransform()
        transform.translate(-self.diameter/2, -self.diameter/2)
        self.setTransform(transform)

    def set_angles(self, theta, phi):
        self.theta = theta
        self.phi = phi

    def set_pen(self, width=1):
        pen = QPen()
        pen.setWidth(width)

        self.setPen(pen)
        self.pen_width = width