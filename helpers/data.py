from .vtk import read_volume_from_vtk_file

import numpy as np

class Data():
    def __init__(self, config_args):
        self.data_name = config_args['dataset']
        self.dataset_config = config_args['dataset_config']
        self.iterations = config_args['iterations']
        self.isosurface_filter_value = config_args['isosurface_filter_value']
        self.histogram_uncertainty_filter = config_args['histogram_uncertainty_filter']

        self.data_path = f'datasets/{self.data_name}/{self.dataset_config}'
        
        self.load_volumes()
        self.load_uncertainty_stats()
        self.load_angles()
    
    def load_volumes(self):
        opacity_file_name = f'{self.data_path}/{self.data_name}_{self.dataset_config}_{self.iterations}_opacity.vtk'
        self.opacity_volume, self.opacity_reader = read_volume_from_vtk_file(opacity_file_name)

        uncertainty_file_name = f'{self.data_path}/{self.data_name}_{self.dataset_config}_{self.iterations}_uncertainty.vtk'
        self.uncertainty_volume, self.uncertainty_reader = read_volume_from_vtk_file(uncertainty_file_name)
    
    def load_uncertainty_stats(self):
        means_file_name = f'{self.data_path}/uncertainty_means.csv'
        stddev_file_name = f'{self.data_path}/uncertainty_standard_deviations.csv'

        self.uncertainty_means = np.loadtxt(means_file_name, delimiter=",")
        self.uncertainty_means_min_max = [np.min(self.uncertainty_means), np.max(self.uncertainty_means)]
        self.uncertainty_means_shifted = self.shift_heatmap_values(self.uncertainty_means)

        self.uncertainty_stds = np.loadtxt(stddev_file_name, delimiter=",")
        self.uncertainty_stds_min_max = [np.min(self.uncertainty_stds), np.max(self.uncertainty_stds)]
        self.uncertainty_stds_shifted = self.shift_heatmap_values(self.uncertainty_stds)

    def load_angles(self):
        angles_file_name = f'{self.data_path}/angles_{self.dataset_config}__{self.data_name}.csv'
        self.angles = np.loadtxt(angles_file_name, delimiter=",")
        # self.angles_shifted = self.shift_angles(self.angles)

    def get_histogram_data(self, reader, num_bins=20, filter=True):
        data, _ = self.vtk_reader_to_numpy(reader)

        if filter:
            mask = data <= self.histogram_uncertainty_filter
            filtered_data = data[~mask]
            # print(np.unique(filtered_data))
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
