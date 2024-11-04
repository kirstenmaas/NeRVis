import argparse
import yaml

import vtk
import numpy as np
import pdb

import matplotlib.pyplot as plt

from helpers.data import Data
from helpers.preprocess import setup_isosurface, setup_uncertainty_volume, setup_renderer, get_orientation, compute_means_stddevs

def main(config_args):
    data = Data(config_args, prepare_data=True)
    
    iso_contour, iso_mapper, iso_actor = setup_isosurface(data)
    density_volume = setup_uncertainty_volume(data.uncertainty_reader)

    color_volume = None
    if data.model_type == 'ensemble':
        color_volume = setup_uncertainty_volume(data.uncertainty_reader_color)

    iso_renderer, _ = setup_renderer(iso_actor)
    density_renderer, density_render_window = setup_renderer(density_volume, color='White')

    color_renderer, color_render_window = None, None
    if data.model_type == 'ensemble':
        color_renderer, color_render_window = setup_renderer(color_volume, color='White')

    camera = iso_renderer.GetActiveCamera()
    orig_orientation = get_orientation(camera)

    theta_range = np.arange(-180, 181, 15)
    phi_range = np.arange(-180, 181, 15)
    means_color, standard_deviations_color, means_density, standard_deviations_density, heatmap_angles = compute_means_stddevs(theta_range, phi_range, orig_orientation, camera, iso_renderer, density_renderer, color_renderer, data.model_type)

    # pdb.set_trace()

    fig, ax = plt.subplots(figsize=(20, 20))
    im = ax.imshow(means_color)
    cbar = ax.figure.colorbar(im, ax=ax)

    ax.set_xticks(np.arange(len(phi_range)), labels=phi_range)
    ax.set_yticks(np.arange(len(theta_range)), labels=theta_range)
    

    # Loop over data dimensions and create text annotations.
    for i in range(len(theta_range)):
        for j in range(len(phi_range)):
            text = ax.text(j, i, np.around(means_color[i, j], 2),
                        ha="center", va="center", color="w")
    # fig.tight_layout()
    # plt.colorbar()
    plt.savefig('heatmap.png')

    np.savetxt(f'{data.data_path}/density_means.csv', means_density, delimiter=',')
    np.savetxt(f'{data.data_path}/density_standard_deviations.csv', standard_deviations_density, delimiter=',')

    np.savetxt(f'{data.data_path}/heatmap_angles.csv', heatmap_angles, delimiter=',', fmt="%s")

    if data.model_type == 'ensemble':
        np.savetxt(f'{data.data_path}/color_means.csv', means_color, delimiter=',')
        np.savetxt(f'{data.data_path}/color_standard_deviations.csv', standard_deviations_color, delimiter=',')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=True, help="Path to (.yml) config file."
    )

    args = parser.parse_args()
    config_file = args.config

    datasets = ['chair', 'mic', 'drums']
    model_types = ['nn', 'ensemble']
    data_types = ['partial', 'full']

    # datasets = ['chair']
    # model_types = ['ensemble']
    # data_types = ['full']
    
    for dataset in datasets:
        for model_type in model_types:
            for data_type in data_types:
                config_file = f'datasets/{dataset}/{model_type}/{data_type}.yml'
                print(f'config file... {config_file}')

                with open(config_file, "r") as f:
                    config_args = yaml.load(f, Loader=yaml.FullLoader)

                main(config_args)
    # with open(config_file, "r") as f:
    #     config_args = yaml.load(f, Loader=yaml.FullLoader)
    #     main(config_args)