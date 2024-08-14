from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtGui import QTransform, QColor

import numpy as np
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import interp1d
import pdb

from .pie import Pie
from .scatter_point import ScatterPoint

class CircularHeatmapScene(QGraphicsScene):
    def __init__(self, title, value_data, std_data, training_angles, outer_diameter=400, angle_size=15, is_top=True):
        super(CircularHeatmapScene, self).__init__()

        self.title = title
        self.value_data = value_data
        self.std_data = std_data
        self.training_angles = training_angles

        self.outer_diameter = outer_diameter
        self.outer_radius = outer_diameter / 2
        self.angle_size = angle_size
        self.num_rings = int(90 / angle_size + 1)
        self.num_sectors = (self.num_rings - 1) * 4
        self.total_span = 16*360
        
        self.is_top = is_top

        self.preprocess_value_data()
        self.draw_pies()
        self.set_angles_pies()

        # self.draw_training_points()

    def preprocess_value_data(self):
        value_data = self.value_data

        # normalize data
        self.value_data = (value_data - np.min(value_data)) / (np.max(value_data) - np.min(value_data))

        self.total_theta_range = np.arange(-180, 181, self.angle_size)
        self.total_phi_range = np.arange(-180, 181, self.angle_size)

        self.theta_range = np.arange(-90, 91, self.angle_size)
        self.phi_range = np.arange(-90, 91, self.angle_size)
        
        self.theta_range_bottom = np.arange(-90, 91, self.angle_size)
        self.phi_range_bottom = [self.convert_angle_to_range(phi) for phi in np.arange(-90, 91, self.angle_size) + 180]#[self.convert_angle_to_range(phi) for phi in np.arange(90, 271, 15)]

    def get_sector_color(self, theta, phi):
        theta_index = int(np.where(self.total_theta_range == theta)[0])
        phi_index = int(np.where(self.total_phi_range == phi)[0])
        data_point = self.value_data[phi_index, theta_index]
        std_point = self.std_data[phi_index, theta_index]
        
        cmap_start = np.array([255, 255, 255]) / 255
        if 'color' in self.title.lower():
            # green
            cmap_end = np.array([35,139,69]) / 255
        else:
            # purple
            cmap_end = np.array([129, 15, 124]) / 255
        
        cmap = LinearSegmentedColormap.from_list('custom_cmap', [cmap_start, cmap_end])

        rgba = np.array(cmap(data_point))
        rgb = rgba[:3] * 255

        return [rgb, data_point, std_point]

    def draw_pies(self):
        num_rings = self.num_rings
        num_sectors = self.num_sectors

        parent_span_angle = round(self.total_span/num_sectors)

        # draw the pies
        pies = []
        circle_diameters = []
        for circle_index in range(num_rings):
            circle_diameter = (num_rings - circle_index) / (num_rings) * self.outer_diameter
            circle_diameters.append(circle_diameter)

            start_angle = -(1/num_sectors*self.total_span)/2

            for sector_index in range(num_sectors):
                parent_pie = Pie(0, circle_diameter, is_top=self.is_top, is_parent_pie=True)

                # middle circle
                if circle_index == num_rings - 1 and sector_index == 0:
                    parent_pie = self.draw_middle_circle(parent_pie)

                    self.addItem(parent_pie)
                    pies.append(parent_pie)
                    break
                else:
                    # temporary: draw 6 individual pies in the span
                    parent_pie.set_as_pie(start_angle, parent_span_angle)

                    self.addItem(parent_pie)
                    pies.append(parent_pie)

                    child_pies = self.draw_child_pies(parent_pie, start_angle, circle_diameter)
                    parent_pie.set_children(child_pies)

                    start_angle += parent_span_angle
        
        self.pies = pies
        self.circle_diameters = circle_diameters[::-1]

    def draw_middle_circle(self, pie):
        theta, phi = [0, 0]
        if not self.is_top:
            theta, phi = [0, 180]
        pie.set_angles(theta, phi)
        color, data_point, std_point = self.get_sector_color(theta, phi)

        pie.set_color(color)
        pie.set_value(data_point)
        return pie

    def draw_child_pies(self, parent_pie, start_angle, circle_diameter):
        # TODO: determine how many to draw and fill
        num_childs = 3
        child_span_angle = round(self.total_span/(self.num_sectors*num_childs))

        child_pies = []
        for i in range(num_childs):
            # don't overdraw the borders to start a smitch later
            child_start_angle = start_angle
            child_diameter = circle_diameter - i*(self.outer_diameter / (self.num_rings*num_childs))
            for j in range(num_childs):
                child_pie = Pie(0, child_diameter, is_top=self.is_top, is_parent_pie=False)
                child_pie.set_as_pie(child_start_angle, child_span_angle-5)
                child_pie.remove_pen()
                child_pie.set_parent_pie(parent_pie)
                child_start_angle += child_span_angle
                
                if i == 1 and j == 1:
                    child_pie.is_std = True
                    child_pie.set_color([0, 0, 0])
                
                self.addItem(child_pie)
                child_pies.append(child_pie)

        return child_pies

    def set_angles_pies(self):
        theta_range = self.theta_range
        phi_range = self.phi_range
        angle_to_radius = interp1d([np.min(np.abs(theta_range)), np.max(np.abs(theta_range))], [0, np.max(np.abs(theta_range))/self.angle_size])

        if not self.is_top:
            theta_range = self.theta_range_bottom
            phi_range = self.phi_range_bottom
            angle_to_radius = interp1d([np.min(np.abs(theta_range)), np.max(np.abs(theta_range))], [0, (np.max(np.abs(theta_range)) - np.min(np.abs(theta_range)))/self.angle_size])
        
        min_radius = self.circle_diameters[0] / 2

        for i, theta in enumerate(theta_range):
            for j, phi in enumerate(phi_range):
                radius = angle_to_radius(abs(theta)) * min_radius + min_radius/2
                if theta < 0:
                    radius *= -1

                alpha = np.deg2rad(phi)
                x, y = self.polar_to_cart(radius, alpha)
                if self.is_top:
                    y *= -1

                item = self.itemAt(x, y, QTransform())
                if item:
                    pie = None
                    if item.is_parent_pie:
                        pie = item
                    elif item.parent_pie:
                        pie = item.parent_pie
                    else:
                        continue

                    if not pie.theta and not pie.phi:
                        color, data_point, std_point = self.get_sector_color(theta, phi)

                        pie.set_color(color)
                        pie.set_value(data_point)

                        pie.set_angles(theta, phi)

                        for child in pie.children:
                            if not child.is_std:
                                child.set_color(color)
                                child.set_value(data_point)

    def draw_training_points(self):
        training_angles = self.training_angles
        min_radius = self.circle_diameters[0] / 2

        theta_range = self.theta_range if self.is_top else self.theta_range_bottom
        phi_range = self.phi_range if self.is_top else self.phi_range_bottom

        training_angle_count = 0

        for angle in training_angles:
            theta, phi = angle

            theta = self.convert_angle_to_range(theta)
            phi = self.convert_angle_to_range(phi)

            if not (self.angle_in_range(theta, theta_range) and self.angle_in_range(phi, phi_range)):
                continue

            training_angle_count += 1

            radius = theta / self.angle_size * min_radius + min_radius
            alpha = np.deg2rad(phi)
            x, y = self.polar_to_cart(radius, alpha)
            if self.is_top:
                y *= -1

            scatter = ScatterPoint(x, y)
            scatter.set_color([0, 0, 0, 0.5*255])

            # get parent pie at x, y
            parent_pie = self.itemAt(x, y, QTransform())
            if parent_pie and parent_pie.is_parent_pie:
                scatter.set_parent_pie(parent_pie)

            self.addItem(scatter)

    def polar_to_cart(self, radius, alpha):
        x = radius * np.cos(alpha)
        y = radius * np.sin(alpha)
        return [x, y]
    
    def convert_angle_to_range(self, angle):
        if angle > 180:
            angle = -(360 - angle)
        return angle
    
    def angle_in_range(self, angle, range):
        return angle <= range[-1] and angle >= range[0]
