from .vtk import read_volume_from_vtk_file
import vtk.util.numpy_support as numpy_support

import pdb
import numpy as np

class Data():
    def __init__(self, config_args, prepare_data=False):
        self.data_name = config_args['dataset']
        self.model_type = config_args['model_type']
        self.dataset_config = config_args['dataset_config']
        self.iterations = config_args['iterations']
        self.isosurface_filter_value = config_args['isosurface_filter_value']
        self.histogram_uncertainty_filter = config_args['histogram_uncertainty_filter']
        self.vmax_density = config_args['vmax_density'] if 'vmax_density' in config_args else 'None'
        self.vmax_color = config_args['vmax_color'] if 'vmax_color' in config_args else 'None'
        self.vmin_std_density = config_args['vmin_std_density'] if 'vmin_std_density' in config_args else 'None'
        self.vmin_std_color = config_args['vmin_std_color'] if 'vmin_std_color' in config_args else 'None'
        self.vmax_std_density = config_args['vmax_std_density'] if 'vmax_std_density' in config_args else 'None'
        self.vmax_std_color = config_args['vmax_std_color'] if 'vmax_std_color' in config_args else 'None'

        self.data_path = f'datasets/{self.data_name}/{self.model_type}/{self.dataset_config}'
        
        self.load_volumes()

        if not prepare_data:
            self.load_uncertainty_stats()
            self.load_angles()

        if self.model_type == 'ensemble':
            self.prepare_2d_plot()
    
    def load_volumes(self):
        opacity_file_name = f'{self.data_path}/{self.data_name}_{self.dataset_config}_{self.iterations}_opacity.vtk'
        self.opacity_volume, self.opacity_reader = read_volume_from_vtk_file(opacity_file_name)

        if self.model_type == 'nn':
            uncertainty_file_name = f'{self.data_path}/{self.data_name}_{self.dataset_config}_{self.iterations}_uncertainty.vtk'
            self.uncertainty_volume, self.uncertainty_reader = read_volume_from_vtk_file(uncertainty_file_name)

            self.filter_nn_uncertainty_volume()
        elif self.model_type == 'ensemble':
            uncertainty_file_name = f'{self.data_path}/{self.data_name}_{self.dataset_config}_{self.iterations}_uncertainty_density.vtk'
            self.uncertainty_volume, self.uncertainty_reader = read_volume_from_vtk_file(uncertainty_file_name)

            uncertainty_file_name = f'{self.data_path}/{self.data_name}_{self.dataset_config}_{self.iterations}_uncertainty_color.vtk'
            self.uncertainty_volume_color, self.uncertainty_reader_color = read_volume_from_vtk_file(uncertainty_file_name)

            self.filter_color_uncertainty_volume()
    
    def filter_color_uncertainty_volume(self):
        # filter out the values lower than the threshold for the color uncertainty volume
        # filter out the density = 0 values from the color uncertainty volume
        uncertainty_color_data = self.uncertainty_reader_color.GetOutput()
        uncertainty_color_scalars = uncertainty_color_data.GetPointData().GetScalars()
        uncertainty_color_scalars_np = numpy_support.vtk_to_numpy(uncertainty_color_scalars)

        density_scalars = self.opacity_reader.GetOutput().GetPointData().GetScalars()
        density_scalars_np = numpy_support.vtk_to_numpy(density_scalars)
        empty_ids = np.argwhere(density_scalars_np < 1e-10)

        uncertainty_color_scalars_np[empty_ids] = 0

        uncertainty_color_scalars = numpy_support.numpy_to_vtk(uncertainty_color_scalars, deep=True)
        uncertainty_color_data.GetPointData().SetScalars(uncertainty_color_scalars)
        self.uncertainty_reader_color.SetOutput(uncertainty_color_data)

    def filter_nn_uncertainty_volume(self):
        # filter out the values lower than the threshold for the nn uncertainty volume
        # filter out the density = 0 values from the nn uncertainty volume
        uncertainty_data = self.uncertainty_reader.GetOutput()
        uncertainty_scalars = uncertainty_data.GetPointData().GetScalars()
        uncertainty_scalars_np = numpy_support.vtk_to_numpy(uncertainty_scalars)

        density_scalars = self.opacity_reader.GetOutput().GetPointData().GetScalars()
        density_scalars_np = numpy_support.vtk_to_numpy(density_scalars)
        empty_ids = np.argwhere(density_scalars_np < 1e-10)
        uncertainty_scalars_np[empty_ids] = 0

        uncertainty_scalars = numpy_support.numpy_to_vtk(uncertainty_scalars, deep=True)
        uncertainty_data.GetPointData().SetScalars(uncertainty_scalars)
        self.uncertainty_reader.SetOutput(uncertainty_data)

    def load_uncertainty_stats(self):
        angles_file_name = f'{self.data_path}/heatmap_angles.csv'
        self.uncertainty_angles = np.genfromtxt(angles_file_name, dtype='str', delimiter=',')
        if self.model_type == 'nn':
            means_file_name = f'{self.data_path}/density_means.csv'
            stddev_file_name = f'{self.data_path}/density_standard_deviations.csv'

            self.uncertainty_means, self.uncertainty_means_min_max = self.load_stats(means_file_name)
            self.uncertainty_stds, self.uncertainty_stds_min_max = self.load_stats(stddev_file_name)
            self.uncertainty_max = self.vmax_density if self.vmax_density != 'None' else np.max(self.uncertainty_means)
            self.uncertainty_stds_min = self.vmin_std_density if self.vmin_std_density != 'None' else np.min(self.uncertainty_stds)
            self.uncertainty_stds_max = self.vmax_std_density if self.vmax_std_density != 'None' else np.max(self.uncertainty_stds)
        elif self.model_type == 'ensemble':
            color_means_file_name = means_file_name = f'{self.data_path}/color_means.csv'
            color_stddev_file_name = f'{self.data_path}/color_standard_deviations.csv'
            density_means_file_name = means_file_name = f'{self.data_path}/density_means.csv'
            density_stddev_file_name = f'{self.data_path}/density_standard_deviations.csv'

            self.color_means, self.color_means_min_max = self.load_stats(color_means_file_name)
            self.color_stds, self.color_stds_min_max = self.load_stats(color_stddev_file_name)
            self.uncertainty_means, self.uncertainty_means_min_max = self.load_stats(density_means_file_name)
            self.uncertainty_stds, self.uncertainty_stds_min_max = self.load_stats(density_stddev_file_name)

            self.uncertainty_max = self.vmax_density if self.vmax_density != 'None' else np.max(self.uncertainty_means)
            self.uncertainty_stds_min = self.vmin_std_density if self.vmin_std_density != 'None' else np.min(self.uncertainty_stds)
            self.uncertainty_stds_max = self.vmax_std_density if self.vmax_std_density != 'None' else np.max(self.uncertainty_stds)

            self.color_max = self.vmax_color if self.vmax_color != 'None' else np.max(self.color_means)
            self.color_stds_min = self.vmin_std_color if self.vmin_std_color != 'None' else np.min(self.color_stds)
            self.color_stds_max = self.vmax_std_color if self.vmax_std_color != 'None' else np.max(self.color_stds)
            
            print('color max', self.color_max)
            print('color stds min-max', self.color_stds_min, self.color_stds_max)
        print('density max', self.uncertainty_max)
        print('uncertainty stds min-max', self.uncertainty_stds_min, self.uncertainty_stds_max)

    def load_stats(self, file_name):
        uncertainty_means = np.loadtxt(file_name, delimiter=",")
        uncertainty_means_min_max = [np.min(uncertainty_means), np.max(uncertainty_means)]
        return uncertainty_means, uncertainty_means_min_max

    def load_angles(self):
        angles_file_name = f'{self.data_path}/angles_{self.dataset_config}__{self.data_name}.csv'
        self.angles = np.loadtxt(angles_file_name, delimiter=",")

    def get_histogram_data(self, reader, num_bins=20, filter=True):
        data, _ = self.vtk_reader_to_numpy(reader)

        if filter:
            mask = data <= self.histogram_uncertainty_filter
            filtered_data = data[~mask]
            hist, bin_edges = np.histogram(filtered_data, bins=num_bins, density=False, range=(0.0, 1.0))
        else:
            hist, bin_edges = np.histogram(data, bins=num_bins, density=False, range=(0.0, 1.0))
        hist_norm = hist / np.max(hist)
        
        return hist_norm

    def vtk_reader_to_numpy(self, reader):
        reader_output = reader.GetOutput()
        dims = reader_output.GetDimensions()

        array_values = []

        # Print the values for all structured points
        for z in range(dims[2]):
            for y in range(dims[1]):
                for x in range(dims[0]):
                    idx = x + dims[0] * (y + dims[1] * z)
                    value = reader_output.GetScalarComponentAsFloat(x, y, z, 0)
                    array_values.append(value)
        arr_value = np.array(array_values)

        return arr_value, dims
    
    def shift_heatmap_values(self, values):
        half_size = int(np.floor(values.shape[1]/2))
        
        x_shift = np.zeros_like(values)
        x_shift[:, :-1] = np.hstack((values[:, half_size:values.shape[1]], values[:, 1:half_size]))
        x_shift[:, -1] = x_shift[:, 0]

        values_shift = np.zeros_like(values)
        values_shift[:-1, :] = np.vstack((x_shift[half_size:values.shape[0], :], x_shift[1:half_size, :]))
        values_shift[-1, :] = values_shift[0, :]

        return values_shift
    
    def shift_angles(self, angles):
        # Shift angles in the y-axis
        angles_shift_y = []
        for i in range(len(angles)):
            angle_y_shifted = angles[i][1] if angles[i][1]==0 or angles[i][1]==360 else 360.0-angles[i][1]
            angles_shift_y.append([angles[i][0], angle_y_shifted])

        # Shift angles in both x and y axes
        angles_list = []
        for i in range(len(angles_shift_y)):
            angle_x_shifted = angles_shift_y[i][0]+180.0 if angles_shift_y[i][0]<180 else angles_shift_y[i][0]-180.0
            angle_y_shifted = angles_shift_y[i][1]+180.0 if angles_shift_y[i][1]<180 else angles_shift_y[i][1]-180.0
            angles_list.append([angle_x_shifted, angle_y_shifted])
        angles = np.array(angles_list)
        return angles

    def prepare_2d_plot(self):
        self.point_colors = numpy_support.vtk_to_numpy(self.uncertainty_volume_color.GetPointData().GetScalars())
        self.point_densities = numpy_support.vtk_to_numpy(self.uncertainty_volume.GetPointData().GetScalars())
        self.point_indices = np.arange(self.point_colors.shape[0]).astype('int')

        filtered_color_ind = np.argwhere(self.point_colors > self.histogram_uncertainty_filter).flatten()
        filtered_density_ind = np.argwhere(self.point_densities > self.histogram_uncertainty_filter).flatten()
        filtered_ind = np.intersect1d(filtered_color_ind, filtered_density_ind)

        scatter_plot_data = np.column_stack((self.point_colors, self.point_densities, self.point_indices))

        self.scatter_plot_data = scatter_plot_data[filtered_ind]