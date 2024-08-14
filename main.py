from components.renderers.interactors import IsoSurfaceWindow, UncertaintyVolWindow
from components.main_layout import MainLayout
from components.renderers.plane_widget import CustomPlaneWidget
from components.renderers.synthesis_view import SynthesisView
from components.transfervis.transfer_function import TransferFunction
from components.transfervis.surface_histogram import SurfaceHistogram
from components.transfervis.surface_radio_button import SurfaceRadioButton
from components.heatmaps.circular_heatmap_layout import CircularHeatmapLayout

from helpers.data import Data
from helpers.zbuffer import ZBuffer
from helpers.camera import CustomCamera

import argparse
import yaml

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
)

def main(config_args):
    app = QApplication(['NeRFDeltaView'])

    window = QMainWindow()
    main_widget = QWidget()
    window.setCentralWidget(main_widget)

    main_layout = MainLayout(main_widget)
    data = Data(config_args)
    
    camera = CustomCamera()
    z_buffer = ZBuffer()

    # renderers
    isosurface_window = IsoSurfaceWindow(main_layout.isosurface_frame, data.opacity_volume, data.isosurface_filter_value, z_buffer, camera)
    
    uncertainty_window_name = 'Uncertainty' if data.model_type == 'nn' else 'Uncertainty: density'
    uncertainty_window = UncertaintyVolWindow(main_layout.uncertainty_vol_frame, data.opacity_reader, data.uncertainty_reader, z_buffer, camera, name=uncertainty_window_name)
    
    plane_widget_mappers = [isosurface_window.mapper, uncertainty_window.density_mapper, uncertainty_window.uncertainty_mapper]
    plane_widget_windows = [isosurface_window, uncertainty_window]
    if data.model_type == 'ensemble':
        color_uncertainty_window_name = 'Uncertainty: color'
        color_uncertainty_window = UncertaintyVolWindow(main_layout.uncertainty_color_frame, data.opacity_reader, data.uncertainty_reader_color, z_buffer, camera, name=color_uncertainty_window_name)
        
        plane_widget_mappers.append(color_uncertainty_window.density_mapper)
        plane_widget_mappers.append(color_uncertainty_window.uncertainty_mapper)

        plane_widget_windows.append(color_uncertainty_window)
    
    plane_widget = CustomPlaneWidget(plane_widget_mappers, plane_widget_windows, z_buffer)
    synthesis_view = SynthesisView(main_layout.synthesis_frame)
    
    # transfer functions
    tf_x_label = 'Uncertainty value' if data.model_type == 'nn' else 'Uncertainty density value'
    tf_title = 'Uncertainty transfer function' if data.model_type == 'nn' else 'Uncertainty density transfer function'
    transfer_function = TransferFunction(main_layout.vis_tab_widget.tf_density_frame, tf_title, tf_x_label, 'Optical property', \
                                         uncertainty_window.uncertainty_color_tf, uncertainty_window.uncertainty_opacity_tf, \
                                            data.get_histogram_data(data.uncertainty_reader), uncertainty_window)

    if data.model_type == 'ensemble':
        tf_x_label = 'Uncertainty color value'
        tf_title = 'Uncertainty color transfer function'
        transfer_function = TransferFunction(main_layout.vis_tab_widget.tf_color_frame, tf_title, tf_x_label, 'Optical property', \
                                            color_uncertainty_window.uncertainty_color_tf, color_uncertainty_window.uncertainty_opacity_tf, \
                                                data.get_histogram_data(data.uncertainty_reader_color), color_uncertainty_window)

    surface_histogram = SurfaceHistogram(main_layout.vis_tab_widget.tf_scalar_graph_frame, 'Isosurface histogram', 'Isosurface value', 'Frequency', \
                                         data.get_histogram_data(data.opacity_reader, filter=False), data.isosurface_filter_value)
    surface_radio_button = SurfaceRadioButton(main_layout.vis_tab_widget.tf_scalar_control_frame, surface_histogram, uncertainty_window)
    
    # heatmaps
    all_heatmaps = []
    heatmap_title = 'Uncertainty for sphere top' if data.model_type == 'nn' else 'Density uncertainty for sphere top'
    mean_heatmap_top = CircularHeatmapLayout(main_layout.vis_tab_widget.mean_heatmap_frame_top, heatmap_title, value_data=data.uncertainty_means_shifted, std_data=data.uncertainty_stds_shifted, training_angles=data.angles, camera=camera)
    heatmap_title = 'Uncertainty for sphere bottom' if data.model_type == 'nn' else 'Density uncertainty for sphere bottom'
    mean_heatmap_bottom = CircularHeatmapLayout(main_layout.vis_tab_widget.mean_heatmap_frame_bottom, heatmap_title, value_data=data.uncertainty_means_shifted, std_data=data.uncertainty_stds_shifted, training_angles=data.angles, camera=camera, is_top=False)    
    
    all_heatmaps.append(mean_heatmap_top)
    all_heatmaps.append(mean_heatmap_bottom)

    if data.model_type == 'ensemble':
        mean_color_heatmap_top = CircularHeatmapLayout(main_layout.vis_tab_widget.mean_color_heatmap_frame_top, 'Color uncertainty for sphere top', value_data=data.color_means_shifted, training_angles=data.angles, camera=camera)
        mean_color_heatmap_bottom = CircularHeatmapLayout(main_layout.vis_tab_widget.mean_color_heatmap_frame_bottom, 'Color uncertainty for sphere bottom', value_data=data.color_means_shifted, training_angles=data.angles, camera=camera, is_top=False)

        all_heatmaps.append(mean_color_heatmap_top)
        all_heatmaps.append(mean_color_heatmap_bottom)

    for i, curr_heatmap in enumerate(all_heatmaps):
        other_heatmaps = [heatmap for heatmap in all_heatmaps if heatmap != curr_heatmap]
        curr_heatmap.set_other_heatmap_layouts(other_heatmaps)

    window.show()

    # initial render
    z_buffer.update_buffer()

    try:
        app.exec()
    except AttributeError:
        app.exec_()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=True, help="Path to (.yml) config file."
    )

    args = parser.parse_args()

    with open(args.config, "r") as f:
        config_args = yaml.load(f, Loader=yaml.FullLoader)

    main(config_args)
