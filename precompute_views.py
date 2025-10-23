import pandas as pd
import yaml
import os
import numpy as np
import time

from helpers.data import Data
from helpers.camera import CustomCamera
from components.renderers.synthesis_button import infer_nerf

from helpers.preprocess import setup_isosurface, setup_renderer, get_orientation, set_orientation

angle_df = pd.read_csv('drawn_heatmap_pies.csv')

# datasets = ['mic', 'drums', 'chair']
# model_types = ['nn', 'ensemble']
# data_types = ['full', 'partial']
# for dataset in datasets:
#     for model_type in model_types:
#         for data_type in data_types:
            # start_time = time.time()

dataset = 'mic'
model_type = 'ensemble'
data_type = 'full'
config_file = f'datasets/{dataset}/{model_type}/{data_type}.yml'
print(f'config file... {config_file}')

with open(config_file, "r") as f:
    config_args = yaml.load(f, Loader=yaml.FullLoader)

data = Data(config_args)

save_folder_name = f'datasets/{dataset}/{model_type}/{data_type}/precomputed_views/'
if not os.path.exists(save_folder_name):
    os.makedirs(save_folder_name)

iso_contour, iso_mapper, iso_actor = setup_isosurface(data)
iso_renderer, _ = setup_renderer(iso_actor)
camera = iso_renderer.GetActiveCamera()
orig_orientation = get_orientation(camera)


# row = angle_df[(np.around(angle_df['azimuth'], 2) == 82.95) & (np.around(angle_df['elevation'], 2) == 135.22)].iloc[0]

start_time = time.time()

for index, row in angle_df.iterrows():
    set_orientation(iso_renderer, orig_orientation)

    print(row['azimuth'], row['elevation'], row['id'])

    index_file_name = str(int(row['id'])).zfill(4) + '.png'
    save_file_name = os.path.join(save_folder_name, index_file_name)

    camera.Azimuth(row['azimuth'])
    camera.Elevation(row['elevation'])
    iso_renderer.ResetCamera()
    camera.OrthogonalizeViewUp()
    infer_nerf(save_file_name, camera, data)

end_time = time.time()
print('Total time for precomputing views:', end_time - start_time)