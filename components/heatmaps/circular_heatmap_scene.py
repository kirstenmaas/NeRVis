from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtGui import QTransform, QColor

import numpy as np
import matplotlib
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import interp1d

from .pie import Pie
from .scatter_point import ScatterPoint

class CircularHeatmapScene(QGraphicsScene):
    def __init__(self, value_data, training_angles, outer_diameter=400, angle_size=15, is_top=True):
        super(CircularHeatmapScene, self).__init__()

        self.value_data = value_data
        self.training_angles = training_angles

        self.outer_diameter = outer_diameter
        self.outer_radius = outer_diameter / 2
        self.angle_size = angle_size
        self.num_rings = int(90 / angle_size + 1)
        self.num_sectors = (self.num_rings - 1) * 4
        
        self.is_top = is_top

        self.preprocess_value_data()
        self.draw_pies()
        self.draw_spherical_points()

        # self.draw_training_points()

    def preprocess_value_data(self):
        value_data = self.value_data
        is_top = self.is_top

        # normalize data
        self.value_data = (value_data - np.min(value_data)) / (np.max(value_data) - np.min(value_data))

        if is_top:
            self.theta_range = np.arange(-180, 181, 15)
            self.phi_range = np.arange(-180, 181, 15)
        else:
            self.theta_range = np.arange(-180, 181, 15)
            self.phi_range = np.arange(-180, 181, 15)

    def get_sector_color(self, theta, phi):
        theta_index = int(np.where(self.theta_range == theta)[0])
        phi_index = int(np.where(self.phi_range == phi)[0])
        data_point = self.value_data[phi_index, theta_index]
        
        cmap = matplotlib.cm.get_cmap('Reds')
        rgba = np.array(cmap(data_point))
        rgb = rgba[:3] * 255

        return rgb

    def draw_pies(self):
        num_rings = self.num_rings
        num_sectors = self.num_sectors

        total_span = 16*360
        quarter_sector_index = num_sectors / 4

        sector_angles = np.concatenate((np.arange(0, 76, 15), np.arange(0, 91, 15)[::-1]))
        circle_angles = np.concatenate((np.arange(0, 90+1, 15)[::-1], -np.arange(0, 90+1, 15), -np.arange(0, 90, 15)[::-1]))

        # draw the pies
        pies = []
        circle_diameters = []
        for circle_index in range(num_rings):
            circle_diameter = (num_rings - circle_index) / (num_rings) * self.outer_diameter
            circle_diameters.append(circle_diameter)

            start_angle = -(1/num_sectors*total_span)/2

            if circle_index == num_rings - 1:
                pie = Pie(0, circle_diameter)
                # pie.set_as_pie(start_angle, total_span)
                theta, phi = [0, 0]

                pie.set_angles(theta, phi)
                
                pie.set_color(self.get_sector_color(theta, phi))
                self.addItem(pie)
                continue

            for sector_index in range(num_sectors):
                
                span_angle = round(1/num_sectors*total_span)

                pie = Pie(0, circle_diameter)
                pie.set_as_pie(start_angle, span_angle)
                
                theta = (num_rings - 1 - circle_index) * self.angle_size
                
                # theta is negative if x < 0
                if sector_index > quarter_sector_index and sector_index <= num_sectors - quarter_sector_index:
                    theta *= -1
                
                phi = 0
                if sector_index <= quarter_sector_index:
                    phi = sector_index * self.angle_size

                if sector_index == quarter_sector_index:
                    theta = 0
                    phi = (num_rings - 1 - circle_index) * self.angle_size

                pie.set_angles(theta, phi)

                pie.set_color(self.get_sector_color(theta, phi))

                self.addItem(pie)

                start_angle += span_angle

                pies.append(pie)
        
        self.pies = pies
        self.circle_diameters = circle_diameters[::-1]
    
    def draw_training_points(self):
        training_angles = self.training_angles

        circle_diameters = self.circle_diameters
        min_radius = circle_diameters[0] / 2
        max_radius = circle_diameters[-2] / 2

        for angle in training_angles:
            color = [0, 0, 0]

            theta = angle[0]
            phi = angle[1]

            if theta > 180:
                # convert to [-180, 180] range
                theta = -(360 - theta)
            if phi > 180:
                # convert to [-180, 180] range
                phi = -(360 - phi)

            if theta > self.theta_range[-1] or theta < self.theta_range[0]:
                continue

            if phi > self.phi_range[-1] or phi < self.phi_range[0]:
                continue

            radius = (theta / 90) * max_radius + min_radius
            alpha = np.deg2rad(phi)

            if radius < 0:
                alpha *= -1

            # angles to polar coordinates
            x = radius * np.cos(alpha)
            y = -radius * np.sin(alpha)
            
            scatter = ScatterPoint(x, y)
            scatter.set_color(color)
            self.addItem(scatter)

    def draw_spherical_points(self):
        angles = [[0, 0], [90, 0], [0, 90]]

        for angle in angles:
            theta, phi = angle
            theta = np.deg2rad(90 - theta)
            phi = np.deg2rad(phi)

            x = self.outer_radius * np.sin(theta) * np.cos(phi)
            y = self.outer_radius * np.sin(theta) * np.sin(phi)
            z = self.outer_radius * np.cos(theta)
            print(x, y, z)

            scatter = ScatterPoint(x, y)
            scatter.set_color([255, 0, 0])
            self.addItem(scatter)