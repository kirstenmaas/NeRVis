from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PyQt6.QtGui import QTransform, QPen, QColor
from PyQt6.QtCore import Qt

import numpy as np
import pdb

class Pie(QGraphicsEllipseItem):
    def __init__(self, xy, diameter, is_top=True, is_parent_pie=False):
        super(QGraphicsEllipseItem, self).__init__(xy, xy, diameter, diameter) 

        self.is_parent_pie = is_parent_pie
        self.is_top = is_top
        self.diameter = diameter

        self.set_transform()
        self.set_pen()

        self.is_std = False

        self.theta = None
        self.phi = None
        self.parent_pie = None
        self.children = []

    def set_as_pie(self, start_angle, span_angle):
        self.setStartAngle(start_angle)
        self.setSpanAngle(span_angle)

    def set_color(self, color):
        brush = QColor(color[0], color[1], color[2])
        self.setBrush(brush)

    def set_value(self, value):
        self.value = value

    def set_transform(self):
        transform = QTransform()
        transform.translate(-self.diameter/2, -self.diameter/2)
        self.setTransform(transform)

    def set_angles(self, theta, phi):
        self.theta = self.range_lower_than_90(theta)
        self.phi = self.range_lower_than_90(phi)

        self.azimuth, self.elevation = self.thetaphi_to_azel(np.deg2rad(self.theta), np.deg2rad(self.phi))

        # correct for bottom sphere
        if not self.is_top:
            self.elevation += 180

        for child_pie in self.children:
            child_pie.set_angles(theta, phi)

    def set_pen(self, width=1):
        pen = QPen()
        pen.setWidth(width)

        self.setPen(pen)
        self.pen_width = width

    def remove_pen(self):
        pen = QPen()

        pen.setStyle(Qt.PenStyle.NoPen)
        self.setPen(pen)
        self.pen_width = 0

    def thetaphi_to_azel(self, theta, phi):
        sin_el = np.sin(phi) * np.sin(theta)
        tan_az = np.cos(phi) * np.tan(theta)
        el = np.arcsin(sin_el)
        az = np.arctan(tan_az)

        el = np.rad2deg(el)
        az = np.rad2deg(az)
        
        return az, el
    
    def range_lower_than_90(self, angle):
        # set angle to +-85 to avoid parallel view plane
        if int(np.abs(angle)) == 90:
            sign = angle/90
            angle = sign * (np.abs(angle) - 5)
        return angle
    
    def set_parent_pie(self, pie):
        self.parent_pie = pie

    def set_children(self, pies):
        self.children = pies