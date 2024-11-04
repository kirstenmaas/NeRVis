from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtGui import QTransform, QColor

import numpy as np
from matplotlib import cm
from scipy.interpolate import interp1d
import pdb

from .pie import Pie
from .scatter_point import ScatterPoint

from helpers.vtk import range_lower_than_90

class CircularHeatmapScene(QGraphicsScene):
    def __init__(self, title, value_data, std_data, vmax, vmin_std, vmax_std, heatmap_angles, training_angles, outer_diameter=400, angle_size=15, is_top=True):
        super(CircularHeatmapScene, self).__init__()

        self.title = title
        self.value_data = value_data
        self.std_data = std_data
        self.vmax = vmax
        self.vmin_std = vmin_std
        self.vmax_std = vmax_std
        self.heatmap_angles = heatmap_angles
        self.training_angles = training_angles

        self.outer_diameter = outer_diameter
        self.outer_radius = outer_diameter / 2
        self.angle_size = angle_size
        self.num_rings = int(90 / angle_size + 1)
        self.num_sectors = (self.num_rings - 1) * 4
        self.total_span = 16*360
        
        self.is_top = is_top

        self.set_theta_phi_ranges()
        self.draw_pies()
        self.set_angles_pies()
        self.draw_child_pies()

        self.draw_training_points()

    def set_theta_phi_ranges(self):
        self.total_theta_range = np.arange(-180, 181, self.angle_size)
        self.total_phi_range = np.arange(-180, 181, self.angle_size)

        self.theta_range = np.arange(-90, 91, self.angle_size)
        self.phi_range = np.arange(-90, 91, self.angle_size)
        
        self.theta_range_bottom = np.arange(-90, 91, self.angle_size)
        self.phi_range_bottom = [self.convert_angle_to_range(phi) for phi in np.arange(-90, 91, self.angle_size) + 180]#[self.convert_angle_to_range(phi) for phi in np.arange(90, 271, 15)]

    def get_sector_color(self, theta, phi):
        heatmap_angles = self.heatmap_angles

        theta = int(range_lower_than_90(theta))
        phi = int(range_lower_than_90(phi))

        angle_str = f'{theta}-{phi}'
        
        angle_index = np.argwhere(heatmap_angles == angle_str)
        if len(angle_index) > 0:
            theta_index, phi_index = angle_index[0]

        data_point = self.value_data[theta_index, phi_index]
        std_point = self.std_data[theta_index, phi_index]
        
        cmap_start = np.array([255, 255, 255]) / 255
        if 'color' in self.title.lower():
            custom_range = [0.1, 0.9]
            custom_cmap = cm.get_cmap('viridis', 100)
        else:
            custom_range = [0.1, 0.9]
            custom_cmap = cm.get_cmap('inferno', 100)
        
        value_in_range = np.interp(data_point, [0, self.vmax], custom_range)

        rgba = np.array(custom_cmap(value_in_range))
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
                parent_pie.remove_pen()

                # middle circle
                if circle_index == num_rings - 1 and sector_index == 0:
                    parent_pie = self.draw_middle_circle(parent_pie)
                    parent_pie.set_as_pie(start_angle, parent_span_angle*num_sectors)
                    parent_pie.is_circle = True

                    self.addItem(parent_pie)
                    pies.append(parent_pie)
                    break
                else:
                    # temporary: draw 6 individual pies in the span
                    parent_pie.set_as_pie(start_angle, parent_span_angle)

                    self.addItem(parent_pie)
                    pies.append(parent_pie)

                    start_angle += parent_span_angle

        self.pies = pies
        self.circle_diameters = circle_diameters[::-1]

    def draw_middle_circle(self, pie):
        theta, phi = [0, 0]
        if not self.is_top:
            theta, phi = [0, 180]
        pie.set_angles(theta, phi)
        color, data_point, std_point = self.get_sector_color(theta, phi)

        pie.set_child_color(color)
        pie.set_color([255, 255, 255])
        pie.set_value(data_point)
        return pie

    def get_child_pies(self, std_point, parent_pie, parent_start_angle, parent_span_angle, circle_diameter, diviser=4):
        minimal_span_angle = parent_span_angle / diviser
        maximal_span_angle = parent_span_angle - minimal_span_angle
        std_to_span_angle = interp1d([self.vmin_std, self.vmax_std], [maximal_span_angle, minimal_span_angle])

        ring_size = (self.outer_diameter / self.num_rings) / 2
        maximal_diameter = circle_diameter - ring_size / diviser
        minimal_diameter = circle_diameter - (ring_size - ring_size / diviser)
        std_to_diameter = interp1d([self.vmin_std, self.vmax_std], [maximal_diameter, minimal_diameter])

        child_pies = []

        # keep the same span angle if the pie is a circle
        # also adjust the sizing of the area accordingly
        if parent_pie.is_circle:
            std_span_angle = parent_span_angle
            std_start_angle = parent_start_angle

            minimal_diameter = circle_diameter / diviser
            maximal_diameter = circle_diameter - minimal_diameter
            std_to_diameter = interp1d([self.vmin_std, self.vmax_std], [maximal_diameter, minimal_diameter])
        else:
            std_span_angle = int(std_to_span_angle(std_point))
            std_start_angle = parent_start_angle + (parent_span_angle-std_span_angle)/2

        std_diameter = int(std_to_diameter(std_point))

        std_child_pie = Pie(0, std_diameter, is_top=self.is_top, is_parent_pie=False)
        std_child_pie.set_as_pie(std_start_angle, std_span_angle)
        std_child_pie.remove_pen()
        std_child_pie.set_parent_pie(parent_pie)
        std_child_pie.is_std = True

        std_child_pie.set_color(parent_pie.child_color, opacity=int(1*255))
        # std_child_pie.set_color([0, 0, 0], opacity=int(1*255))
        child_pies.append(std_child_pie)

        # cover up the bottom ring part with a new pie
        if not parent_pie.is_circle:
            bottom_ring_diameter = (circle_diameter - std_diameter) + circle_diameter - ring_size*2
            bottom_ring_pie = Pie(0, bottom_ring_diameter, is_top=self.is_top, is_parent_pie=False)
            bottom_ring_pie.set_as_pie(parent_start_angle, parent_span_angle)
            bottom_ring_pie.remove_pen()
            bottom_ring_pie.set_color(parent_pie.color)
            bottom_ring_pie.set_parent_pie(parent_pie)
            child_pies.append(bottom_ring_pie)

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
                
                # rotate the heatmaps so that they line up nicely top-bottom
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

                    set_phi = phi
                    set_theta = theta
                    if self.is_top and int(np.abs(phi)) == 90:
                        set_phi = theta*np.sign(phi)
                        set_theta = 0

                    if not pie.theta and not pie.phi:
                        pie.set_color_angles(set_theta, set_phi)

                        color, data_point, std_point = self.get_sector_color(set_theta, set_phi)

                        pie.set_child_color(color)
                        pie.set_color([255, 255, 255])
                        pie.set_value(data_point)

                        pie.set_angles(theta, phi)

                    child_pies = self.get_child_pies(std_point, pie, pie.start_angle, pie.span_angle, pie.diameter)
                    pie.set_children(child_pies)

    def draw_child_pies(self):

        # remove all the drawn pies
        for pie in self.pies:
            self.removeItem(pie)
        
        # redraw the pies one by one so they are visible in z direction correctly
        for pie in self.pies:
            self.addItem(pie)

            for child_pie in pie.children:
                self.addItem(child_pie)

            border_pie = Pie(0, pie.diameter, pie.is_top)
            border_pie.set_as_pie(pie.start_angle, pie.span_angle)
            border_pie.set_parent_pie(pie)
            pie.set_border_pie(border_pie)
            self.addItem(border_pie)

    def draw_training_points(self):
        # training_angles = [
        #     [0, 15],
        #     [0, 30],
        #     [0, 45]
        # ]

        training_angles = self.training_angles
        min_radius = self.circle_diameters[0] / 2

        theta_range = self.theta_range
        phi_range = self.phi_range
        angle_to_radius = interp1d([np.min(np.abs(theta_range)), np.max(np.abs(theta_range))], [0, np.max(np.abs(theta_range))/self.angle_size])

        if not self.is_top:
            theta_range = self.theta_range_bottom
            phi_range = self.phi_range_bottom
            angle_to_radius = interp1d([np.min(np.abs(theta_range)), np.max(np.abs(theta_range))], [0, (np.max(np.abs(theta_range)) - np.min(np.abs(theta_range)))/self.angle_size])

        num_training_point = 0
        for angle in training_angles:
            theta, phi = angle

            # pole
            if np.abs(theta) < self.angle_size and int(np.abs(phi)) > 0:
                sign = -1 if theta < 0 else 1
                phi = sign * (90 - np.abs(theta))
                theta = angle[1]

            theta = self.convert_angle_to_range(theta)
            phi = self.convert_angle_to_range(phi)

            if not (self.angle_in_range(theta, theta_range) and self.angle_in_range(phi, phi_range)):
                continue

            radius = angle_to_radius(abs(theta)) * min_radius
            if int(theta) != 0 or int(phi) != 0:
                radius += min_radius
            
            if theta < 0:
                radius *= -1

            alpha = np.deg2rad(phi)
            y, x = self.polar_to_cart(radius, alpha)
            if self.is_top:
                y *= -1

            scatter = ScatterPoint(x, y)
            scatter.set_color([125,125,125, int(255)])

            # get parent pie at x, y
            parent_pie = self.itemAt(x, y, QTransform())
            if parent_pie and parent_pie.is_parent_pie:
                scatter.set_parent_pie(parent_pie)

            self.addItem(scatter)
            num_training_point += 1

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
