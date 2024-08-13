import os
import vtk
import numpy as np
import configargparse
import pdb

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
    QHBoxLayout,
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
    uncertainty_window = UncertaintyVolWindow(main_layout.uncertainty_vol_frame, data.opacity_reader, data.uncertainty_reader, z_buffer, camera)
    # plane_widget = CustomPlaneWidget([isosurface_window.mapper, uncertainty_window.density_mapper, uncertainty_window.uncertainty_mapper], [isosurface_window, uncertainty_window], z_buffer)
    synthesis_view = SynthesisView(main_layout.synthesis_frame)
    
    # transfer functions
    transfer_function = TransferFunction(main_layout.vis_tab_widget.tf_tf_frame, 'Uncertainty transfer function', 'Uncertainty value', 'Optical property', \
                                         uncertainty_window.uncertainty_color_tf, uncertainty_window.uncertainty_opacity_tf, \
                                            data.get_histogram_data(data.uncertainty_reader), uncertainty_window)

    surface_histogram = SurfaceHistogram(main_layout.vis_tab_widget.tf_scalar_graph_frame, 'Isosurface histogram', 'Isosurface value', 'Frequency', \
                                         data.get_histogram_data(data.opacity_reader, filter=False), data.isosurface_filter_value)
    surface_radio_button = SurfaceRadioButton(main_layout.vis_tab_widget.tf_scalar_control_frame, surface_histogram, uncertainty_window)
    
    # heatmaps
    mean_heatmap_top = CircularHeatmapLayout(main_layout.vis_tab_widget.mean_heatmap_frame, value_data=data.uncertainty_means_shifted, training_angles=data.angles, camera=camera)    

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
