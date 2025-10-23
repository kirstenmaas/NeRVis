from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtGui import QTransform, QColor

import numpy as np
from matplotlib import cm
from scipy.interpolate import interp1d
import pdb
import copy
import pandas as pd
import os

from .pie import Pie
from .scatter_point import ScatterPoint

from helpers.vtk import range_lower_than_90

class CircularHeatmapScene(QGraphicsScene):
    def __init__(self, title, value_data, std_data, max_data, 
                 vmax, vmin_std, vmax_std, vmin_max, vmax_max,
                 heatmap_angles, training_angles, outer_diameter=400, angle_size=15, is_top=True):
        super(CircularHeatmapScene, self).__init__()

        self.title = title
        self.value_data = value_data
        self.std_data = std_data
        self.max_data = max_data
        self.vmax = vmax
        self.vmin_std = vmin_std
        self.vmax_std = vmax_std
        self.vmin_max = vmin_max
        self.vmax_max = vmax_max
        self.heatmap_angles = heatmap_angles
        self.training_angles = training_angles

        self.outer_diameter = outer_diameter
        self.outer_radius = outer_diameter / 2
        self.angle_size = angle_size
        self.num_rings = int(90 / angle_size + 1)
        self.num_sectors = (self.num_rings - 1) * 4
        self.total_span = 16*360

        self.projection_type = 'Equidistant' # Equidistant | Equal-area
        self.pies = []
        self.scatters = []
        
        self.is_top = is_top

        self.set_theta_phi_ranges()
        self.set_extreme_type()
        self.draw_pies()
        self.draw_training_points()

    def set_extreme_type(self, type='Standard deviation'):
        self.extreme_type = type  # 'std' or 'max'
        self.extreme_data = self.std_data if type == 'Standard deviation' else self.max_data
        self.vmin_extreme = self.vmin_std if type == 'Standard deviation' else self.vmin_max
        self.vmax_extreme = self.vmax_std if type == 'Standard deviation' else self.vmax_max

    def sph_to_cart_equi(self, theta, phi):
        angle_to_radius = interp1d([np.min(np.abs(self.theta_range)), np.max(np.abs(self.theta_range))], 
                                   [1, self.num_rings+1])
        
        cart_radius = angle_to_radius(abs(theta))
        if cart_radius != 1:
            cart_radius -= 0.5
        else:
            cart_radius = 0
        cart_radius = cart_radius/(self.num_rings+1)
        if theta < 0:
            cart_radius *= -1
        
        # rotate the heatmaps so that they line up nicely top-bottom
        radius_equi = angle_to_radius(abs(theta)) / (self.num_rings+1)
        if theta < 0:
            radius_equi *= -1
        alpha_equi = np.deg2rad(phi)

        # equidistant
        coordinate_twod = self.polar_to_cart(cart_radius, alpha_equi)
        
        if self.is_top:
            coordinate_twod[1] *= -1

        coordinate_polar = np.array([self.outer_radius*radius_equi, alpha_equi])
        
        # from radius negative and phi [-90, 90] to positive radius and phi [0, 360]
        polar_pos = self.cart_to_polar(coordinate_twod[0], coordinate_twod[1])
        coordinate_polar[0] = np.sign(polar_pos[0]) * abs(coordinate_polar[0])
        coordinate_polar[1] = polar_pos[1]

        return [coordinate_twod, coordinate_polar]

    def sph_to_cart_area(self, theta, phi, area_fraction=1/2):
        # it is not exactly an equal area but it represents the idea of it
        
        theta_fr = np.abs(theta)
        if theta_fr != 0:
            theta_fr -= self.angle_size / 2

        radius_area = (theta_fr / np.max(self.theta_range))**(area_fraction)
        if theta < 0:
            radius_area *= -1

        alpha_area = np.deg2rad(phi)
        coordinate_twod = self.polar_to_cart(radius_area, alpha_area)
        if self.is_top:
            coordinate_twod[1] *= -1

        coordinate_polar = self.cart_to_polar(coordinate_twod[0], coordinate_twod[1])

        radius_area = ((np.abs(theta) + self.angle_size) / (np.max(self.theta_range) + self.angle_size))**(area_fraction) * self.outer_radius
        coordinate_polar = np.array([radius_area, coordinate_polar[1]])

        return [coordinate_twod, coordinate_polar]

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
        else:
            pdb.set_trace()

        data_point = self.value_data[theta_index, phi_index]
        extreme_point = self.extreme_data[theta_index, phi_index]
        
        if 'color' in self.title.lower():
            custom_range = [0.1, 0.9]
            custom_cmap = cm.get_cmap('viridis', 100)
        else:
            custom_range = [0.1, 0.9]
            custom_cmap = cm.get_cmap('inferno', 100)
        
        value_in_range = np.interp(data_point, [0, self.vmax], custom_range)

        rgba = np.array(custom_cmap(value_in_range))
        rgb = rgba[:3] * 255

        return [rgb, data_point, extreme_point]

    def draw_pies(self):
        num_rings = self.num_rings
        num_sectors = self.num_sectors
        
        theta_range = self.theta_range
        phi_range = self.phi_range
        if not self.is_top:
            theta_range = self.theta_range_bottom
            phi_range = self.phi_range_bottom

        cart_coordinates = []
        polar_coordinates = []
        thetas = []
        phis = []

        for phi in phi_range:
            for theta in theta_range:
                # based on mapping
                if self.projection_type == 'Equal-area':
                    coordinate_twod, coordinate_polar = self.sph_to_cart_area(theta, phi)
                else:
                    coordinate_twod, coordinate_polar = self.sph_to_cart_equi(theta, phi)
                cart_coordinates.append(coordinate_twod)
                polar_coordinates.append(coordinate_polar)
                thetas.append(theta)
                phis.append(phi)

        cart_coordinates = np.array(cart_coordinates)
        polar_coordinates = np.array(polar_coordinates)
        
        pies = []

        start_angle = -(1/num_sectors*self.total_span)/2
        parent_span_angle = round(self.total_span/num_sectors)

        # draw from outer circle to inner circle
        # draw in ascending order of alphas
        unique_radii = np.sort(np.unique(polar_coordinates[:, 0]))[::-1]
        
        unique_radii = np.array([radius for radius in unique_radii if radius > 0])

        for radius in unique_radii:
            radius_ids = np.argwhere(polar_coordinates[:, 0] == radius).flatten()
            alphas = np.unique(polar_coordinates[radius_ids][:, 1])
            
            sorted_alpha_ids = np.argsort(alphas)
            radius_ids_sorted = radius_ids[sorted_alpha_ids]
            for radius_id in radius_ids_sorted:
                radius = polar_coordinates[radius_id, 0]
                alpha = polar_coordinates[radius_id, 1]
                theta = thetas[radius_id]
                phi = phis[radius_id]
                diameter = np.abs(radius * 2)
                parent_start_angle = start_angle + np.rad2deg(alpha)*16

                parent_pie = Pie(0, diameter, is_top=self.is_top, is_parent_pie=True)
                parent_pie.set_as_pie(parent_start_angle, parent_span_angle)

                color_phi = phi
                color_theta = theta
                if self.is_top and int(np.abs(phi)) == 90:
                    color_phi = theta*np.sign(phi)
                    color_theta = 0

                color, data_point, extreme_point = self.get_sector_color(color_theta, color_phi)

                parent_pie.set_color_angles(color_theta, color_phi)
                parent_pie.set_angles(theta, phi)
                parent_pie.set_color([255, 255, 255])
                parent_pie.set_value(data_point)
                parent_pie.set_child_color(color)
                
                self.addItem(parent_pie)
                pies.append(parent_pie)

                # extract the min and max radius
                radius_id = np.argwhere(unique_radii == radius).flatten()[0]
                
                max_diameter = diameter
                min_diameter = (unique_radii[0] - unique_radii[1]) * 2
                if radius_id + 1 < len(unique_radii):
                    min_diameter = unique_radii[radius_id + 1] * 2

                # if radius == unique_radii[0]:
                child_pies = self.get_child_pies(extreme_point, parent_pie, parent_start_angle, parent_span_angle, min_diameter, max_diameter)
                parent_pie.set_children(child_pies)

                for child_pie in child_pies:
                    self.addItem(child_pie)
                
                border_pie = parent_pie.create_border_pie()
                self.addItem(border_pie)

        # draw middle circle
        parent_pie = self.draw_middle_circle(unique_radii)
        pies.append(parent_pie)

        self.pies = pies
        self.store_drawn_pie_angles()

    def draw_middle_circle(self, unique_radii):
        radius = unique_radii[-1]
        if self.projection_type == 'Equidistant':
            radius = unique_radii[-1] / 2

        diameter = radius * 2
        parent_pie = Pie(0, diameter, is_top=self.is_top, is_parent_pie=True)
        theta, phi = [0, 0]
        if not self.is_top:
            theta, phi = [0, 180]

        parent_pie.set_color_angles(theta, phi)
        color, data_point, extreme_point = self.get_sector_color(theta, phi)

        parent_pie.set_angles(theta, phi)
        parent_pie.set_color([255, 255, 255])
        parent_pie.set_value(data_point)
        parent_pie.set_child_color(color)

        start_angle = -(1/self.num_sectors*self.total_span)/2
        parent_pie.is_circle = True
        parent_pie.set_as_pie(start_angle, self.total_span)
        self.addItem(parent_pie)
        
        child_pies = self.get_child_pies(extreme_point, parent_pie, start_angle, self.total_span, 0, parent_pie.diameter)
        parent_pie.set_children(child_pies)
        for child_pie in child_pies:
            self.addItem(child_pie)
        
        border_pie = parent_pie.create_border_pie()
        self.addItem(border_pie)

        return parent_pie

    def get_child_pies(self, extreme_point, parent_pie, parent_start_angle, parent_span_angle, min_diameter, max_diameter, diviser=8):
        minimal_span_angle = parent_span_angle / diviser
        maximal_span_angle = parent_span_angle - minimal_span_angle
        extreme_to_span_angle = interp1d([self.vmin_extreme, self.vmax_extreme], [maximal_span_angle, minimal_span_angle])

        child_pies = []

        ring_size = (max_diameter - min_diameter) / 2
        maximal_diameter = max_diameter #- ring_size / diviser
        minimal_diameter = min_diameter + ring_size + ring_size / diviser

        # # keep the same span angle if the pie is a circle
        # # also adjust the sizing of the area accordingly
        if parent_pie.is_circle:
            extreme_span_angle = parent_span_angle
            extreme_start_angle = parent_start_angle

            maximal_diameter = max_diameter - max_diameter / diviser
            minimal_diameter = max_diameter / diviser
        else:
            extreme_span_angle = int(extreme_to_span_angle(extreme_point))
            extreme_start_angle = parent_start_angle + (parent_span_angle-extreme_span_angle)/2

        norm_extreme_point = 1 - (extreme_point / 2) / (self.vmax_extreme / 2) # we assume std can be zero (fill the whole block)

        extreme_diameter = norm_extreme_point * (maximal_diameter - minimal_diameter) + minimal_diameter

        extreme_child_pie = Pie(0, extreme_diameter, is_top=self.is_top, is_parent_pie=False)
        extreme_child_pie.set_as_pie(extreme_start_angle, extreme_span_angle)
        extreme_child_pie.remove_pen()
        extreme_child_pie.set_parent_pie(parent_pie)
        extreme_child_pie.is_extreme = True

        extreme_child_pie.set_color(parent_pie.child_color, opacity=int(1*255))
        child_pies.append(extreme_child_pie)

        # cover up the bottom ring part with a new pie
        if not parent_pie.is_circle:
            bottom_ring_diameter = (maximal_diameter - extreme_diameter) + min_diameter #+ max_diameter - ring_size*2
            bottom_ring_pie = Pie(0, bottom_ring_diameter, is_top=self.is_top, is_parent_pie=False)
            bottom_ring_pie.set_as_pie(extreme_start_angle, extreme_span_angle)
            bottom_ring_pie.remove_pen()
            bottom_ring_pie.set_color(parent_pie.color)
            bottom_ring_pie.set_parent_pie(parent_pie)
            child_pies.append(bottom_ring_pie)

        return child_pies

    def draw_training_points(self):
        self.scatters = []

        training_angles = self.training_angles

        theta_range = copy.deepcopy(self.theta_range)
        phi_range = copy.deepcopy(self.phi_range)
        if not self.is_top:
            theta_range = copy.deepcopy(self.theta_range_bottom)
            phi_range = copy.deepcopy(self.phi_range_bottom)

        # account for edges of circle (i.e. cells midpoints correspond to actual values)
        theta_range[0] -= self.angle_size/2
        theta_range[1] += self.angle_size/2
        phi_range[0] -= self.angle_size/2
        phi_range[1] += self.angle_size/2

        for training_angle in training_angles:
            theta, phi = training_angle

            if np.abs(theta) < self.angle_size and int(np.abs(phi)) > 0:
                sign = -1 if theta < 0 else 1
                phi = sign * (90 - np.abs(theta))
                theta = training_angle[1]
            
            # convert to [-180, 180] range
            theta = self.convert_angle_to_range(theta)
            phi = self.convert_angle_to_range(phi)
            
            if not (self.angle_in_range(theta, theta_range) and self.angle_in_range(phi, phi_range)):
                continue

            if self.projection_type == 'Equal-area':
                coordinate_twod, _ = self.sph_to_cart_area(theta, phi)
            else:
                coordinate_twod, _ = self.sph_to_cart_equi(theta, phi)

            coordinate_twod = coordinate_twod * self.outer_radius
            y, x = coordinate_twod

            scatter = ScatterPoint(x, y)
            scatter.set_color([255,255,51, int(255)])

            # get parent pie at x, y
            parent_pie = self.itemAt(x, y, QTransform())
            if parent_pie and parent_pie.is_parent_pie:
                scatter.set_parent_pie(parent_pie)

            self.addItem(scatter)
            self.scatters.append(scatter)

    def polar_to_cart(self, radius, alpha):
        x = radius * np.cos(alpha)
        y = radius * np.sin(alpha)
        return np.array([x, y])
    
    def cart_to_polar(self, x, y):
        rad = np.sqrt(x*x + y*y)

        alpha = 0
        if y >= 0 and rad != 0:
            alpha = np.arccos(x / rad)
        elif y < 0:
            alpha = -np.arccos(x / rad)
            
        return rad, alpha
    
    def convert_angle_to_range(self, angle):
        if angle > 180:
            angle = -(360 - angle)
        return angle
    
    def angle_in_range(self, angle, range):
        return angle <= range[-1] and angle >= range[0]
    
    def reset_heatmap(self, projection_type, extreme_type='Standard deviation'):
        self.projection_type = projection_type

        # remove the previous pies, scatters, etc.
        for pie in self.pies:
            for child_pie in pie.children:
                self.removeItem(child_pie)

            self.removeItem(pie.border_pie)
            self.removeItem(pie)
        
        for scatter in self.scatters:
            self.removeItem(scatter)
        
        self.set_extreme_type(extreme_type)
        self.draw_pies()
        self.draw_training_points()

    def store_drawn_pie_angles(self):
        if os.path.exists('drawn_heatmap_pies.csv'):
            old_df = pd.read_csv('drawn_heatmap_pies.csv')
            thetas = old_df['theta'].tolist()
            phis = old_df['phi'].tolist()
            azimuths = old_df['azimuth'].tolist()
            elevations = old_df['elevation'].tolist()
            counters = old_df['id'].tolist()
            counter = len(counters)
        else:
            thetas = []
            phis = []
            azimuths = []
            elevations = []
            counters = []
            counter = 0

        # check if the first pie has already been stored, if so, skip storing at all
        first_theta = self.pies[0].theta
        first_phi = self.pies[0].phi
        if first_theta in thetas and first_phi in phis:
            return

        for pie in self.pies:
            thetas.append(pie.theta)
            phis.append(pie.phi)
            azimuths.append(pie.azimuth)
            elevations.append(pie.elevation)
            counters.append(counter)
            counter += 1
        
        df = pd.DataFrame({ 'id': counters, 'theta': thetas, 'phi': phis, 'azimuth': azimuths, 'elevation': elevations })
        df.to_csv('drawn_heatmap_pies.csv', index=False)

