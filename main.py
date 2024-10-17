from components.renderers.interactors import IsoSurfaceWindow, UncertaintyVolWindow
from components.main_layout import MainLayout
from components.renderers.plane_widget import CustomPlaneWidget
from components.renderers.synthesis_view import SynthesisView
from components.renderers.synthesis_button import SynthesisButton
from components.transfervis.transfer_function import TransferFunction
from components.transfervis.surface_histogram import SurfaceHistogram
from components.transfervis.surface_radio_button import SurfaceRadioButton
from components.heatmaps.circular_heatmap_layout import CircularHeatmapLayout
from components.heatmaps.colorbar import Colorbar
from components.heatmaps.legend import Legend
from components.transfervis.density_scatter_plot import DensityScatterPlot
from components.custom_main_window import CustomMainWindow

from helpers.data import Data
from helpers.zbuffer import ZBuffer
from helpers.camera import CustomCamera

import argparse
import yaml
import sys
import numpy as np

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
)

def main(config_args):
    app = QApplication(['Uncertainty Visualization for NeRFs'])

    window = CustomMainWindow()
    main_widget = QWidget()
    window.setCentralWidget(main_widget)

    main_layout = MainLayout(main_widget)
    data = Data(config_args)
    
    camera = CustomCamera()
    z_buffer = ZBuffer()

    # renderers
    isosurface_window = IsoSurfaceWindow(main_layout.isosurface_vol_frame, data.opacity_volume, data.isosurface_filter_value, z_buffer, camera)
    window.set_interactor(isosurface_window)

    uncertainty_window_name = 'Uncertainty' if data.model_type == 'nn' else 'Density Uncertainty'
    uncertainty_window = UncertaintyVolWindow(main_layout.uncertainty_density_vol_frame, data.opacity_reader, data.uncertainty_reader, z_buffer, camera, name=uncertainty_window_name)
    window.set_interactor(uncertainty_window)

    plane_widget_mappers = [isosurface_window.mapper, uncertainty_window.density_mapper, uncertainty_window.uncertainty_mapper]
    plane_widget_windows = [isosurface_window, uncertainty_window]
    if data.model_type == 'ensemble':
        color_uncertainty_window_name = 'Color Uncertainty'
        color_uncertainty_window = UncertaintyVolWindow(main_layout.uncertainty_color_vol_frame, data.opacity_reader, data.uncertainty_reader_color, z_buffer, camera, name=color_uncertainty_window_name)
        window.set_interactor(color_uncertainty_window)

        plane_widget_mappers.append(color_uncertainty_window.density_mapper)
        plane_widget_mappers.append(color_uncertainty_window.uncertainty_mapper)

        plane_widget_windows.append(color_uncertainty_window)

    plane_widget = CustomPlaneWidget(plane_widget_mappers, plane_widget_windows, z_buffer)

    synthesis_view = SynthesisView(main_layout.synthesis_image_frame)
    synthesis_button = SynthesisButton('Render image', main_layout.synthesis_layout, camera, synthesis_view, data)
    
    # transfer functions
    tf_x_label = 'Uncertainty value' if data.model_type == 'nn' else 'Density uncertainty value'
    tf_title = 'Uncertainty Transfer Function' if data.model_type == 'nn' else 'Density Uncertainty Transfer Function'
    transfer_function = TransferFunction(main_layout.vis_tab_widget.tf_density_frame, tf_title, tf_x_label, 'Optical property', \
                                         uncertainty_window.uncertainty_color_tf, uncertainty_window.uncertainty_opacity_tf, \
                                            data.get_histogram_data(data.uncertainty_reader), uncertainty_window)

    if data.model_type == 'ensemble':
        tf_x_label = 'Color uncertainty value'
        tf_title = 'Color Uncertainty Transfer Function'
        transfer_function = TransferFunction(main_layout.vis_tab_widget.tf_color_frame, tf_title, tf_x_label, 'Optical property', \
                                            color_uncertainty_window.uncertainty_color_tf, color_uncertainty_window.uncertainty_opacity_tf, \
                                                data.get_histogram_data(data.uncertainty_reader_color), color_uncertainty_window)

        density_scatter_plot = DensityScatterPlot(main_layout.vis_tab_widget.tf_distr_frame, data=data.scatter_plot_data, renderer_windows=plane_widget_windows[1:])
        window.set_mpl_plot(density_scatter_plot)

    # surface_histogram = SurfaceHistogram(main_layout.vis_tab_widget.tf_scalar_graph_frame, 'Isosurface Histogram', 'Isosurface value', 'Frequency', \
    #                                      data.get_histogram_data(data.opacity_reader, filter=False), data.isosurface_filter_value)
    surface_radio_button = SurfaceRadioButton(main_layout.isosurface_control_frame, plane_widget_windows[1:])
    
    # heatmaps
    all_heatmaps = []
    heatmap_title = 'Uncertainty - Upper Sphere' if data.model_type == 'nn' else 'Density Uncertainty - Upper Sphere'
    mean_heatmap_top = CircularHeatmapLayout(main_layout.vis_tab_widget.mean_heatmap_frame_top, heatmap_title, value_data=data.uncertainty_means, std_data=data.uncertainty_stds, heatmap_angles=data.uncertainty_angles, training_angles=data.angles, camera=camera)
    
    colorbar_title = 'Uncertainty mean' if data.model_type == 'nn' else 'Density uncertainty mean'
    mean_colorbar = Colorbar(main_layout.vis_tab_widget.mean_heatmap_colorbar, vmin=0, vmax=np.max(data.uncertainty_means), color_str='purple', name=colorbar_title)
    window.set_mpl_plot(mean_colorbar)

    heatmap_title = 'Uncertainty - Lower Sphere' if data.model_type == 'nn' else 'Density uncertainty - Lower Sphere'
    mean_heatmap_bottom = CircularHeatmapLayout(main_layout.vis_tab_widget.mean_heatmap_frame_bottom, heatmap_title, value_data=data.uncertainty_means, std_data=data.uncertainty_stds, heatmap_angles=data.uncertainty_angles, training_angles=data.angles, camera=camera, is_top=False)    
    
    all_heatmaps.append(mean_heatmap_top)
    all_heatmaps.append(mean_heatmap_bottom)

    if data.model_type == 'ensemble':
        mean_color_heatmap_top = CircularHeatmapLayout(main_layout.vis_tab_widget.mean_color_heatmap_frame_top, 'Color Uncertainty - Upper Sphere', value_data=data.color_means, std_data=data.color_stds, heatmap_angles=data.uncertainty_angles, training_angles=data.angles, camera=camera)
        mean_color_heatmap_bottom = CircularHeatmapLayout(main_layout.vis_tab_widget.mean_color_heatmap_frame_bottom, 'Color Uncertainty - Lower Sphere', value_data=data.color_means, std_data=data.color_stds, heatmap_angles=data.uncertainty_angles, training_angles=data.angles, camera=camera, is_top=False)

        color_colorbar = Colorbar(main_layout.vis_tab_widget.mean_color_heatmap_colorbar, vmin=0, vmax=np.max(data.color_means), color_str='green', name='Color uncertainty mean')
        window.set_mpl_plot(color_colorbar)

        all_heatmaps.append(mean_color_heatmap_top)
        all_heatmaps.append(mean_color_heatmap_bottom)

    for i, curr_heatmap in enumerate(all_heatmaps):
        other_heatmaps = [heatmap for heatmap in all_heatmaps if heatmap != curr_heatmap]
        curr_heatmap.set_other_heatmap_layouts(other_heatmaps)

    heatmap_legend = Legend(main_layout.vis_tab_widget.heatmap_legend)

    window.show()

    # initial render
    z_buffer.update_buffer()

    # render initial image
    # synthesis_button.eval_nerf()

    app.exec()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=True, help="Path to (.yml) config file."
    )

    args = parser.parse_args()

    with open(args.config, "r") as f:
        config_args = yaml.load(f, Loader=yaml.FullLoader)

    main(config_args)
