#!/usr/bin/env python

"""
Create a ImageData grid and then assign an uncertainty scalar value and opacity scalar value to each point.
"""

import torch

import argparse
import sys
import os
import time
from datetime import datetime
import pdb
import matplotlib.pyplot as plt
from tqdm import tqdm

import vtk
import pyvista as pv

import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkImagingCore import vtkImageCast
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import vtkDoubleArray, vtkMath, vtkFloatArray
from vtkmodules.vtkIOLegacy import (
    vtkStructuredPointsReader,
    vtkStructuredPointsWriter,
    vtkRectilinearGridWriter,
)
import vtk.util.numpy_support as numpy_support
from vtkmodules.vtkRenderingVolume import (
    vtkFixedPointVolumeRayCastMapper,
)
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkOpenGLRayCastImageDisplayHelper, vtkOpenGLGPUVolumeRayCastMapper
from vtkmodules.vtkCommonTransforms import (
    vtkTransform,
)
from vtkmodules.vtkFiltersGeneral import (
    vtkTransformFilter,
    vtkTransformPolyDataFilter,
)
from vtkmodules.vtkCommonDataModel import (
    vtkPolyData,
    vtkPiecewiseFunction,
    vtkRectilinearGrid,
    vtkImageData,
    vtkStructuredPoints,
    vtkPlane,
)
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer,
    vtkColorTransferFunction,
    vtkVolumeProperty,
    vtkVolume,
)
from vtkmodules.vtkFiltersGeometry import (
    vtkImageDataGeometryFilter,
    vtkRectilinearGridGeometryFilter,
)
from vtkmodules.vtkIOXML import (
    vtkXMLImageDataReader,
    vtkXMLImageDataWriter,
)
from vtkmodules.vtkIOLegacy import (
    vtkUnstructuredGridWriter,
    #vtkImageDataWriter,
)
from vtkmodules.vtkFiltersCore import (
    vtkContourFilter,
    vtkCutter,
    vtkPolyDataNormals,
    vtkStripper,
    vtkStructuredGridOutlineFilter,
    vtkTubeFilter,
    vtkClipPolyData,
)

import numpy as np
import torch
import random
import math
import yaml
#import simplejson

from scipy.spatial.distance import pdist, squareform

from nerf import (CfgNode, models, helpers)

def volume_generator(scene, dataset, model_type, iteration, xyzNumPoint=128):
    xyzMin = -1.5
    xyzMax = 1.5
    batch_size = 2048

    config = f'datasets/{scene}/{model_type}/{dataset}/config.yml'
    load_checkpoint = f'datasets/{scene}/{model_type}/{dataset}/checkpoint{iteration-1}.ckpt'

    # Read config file.
    cfg = None
    with open(config, "r") as f:
        cfg_dict = yaml.load(f, Loader=yaml.FullLoader)
        cfg = CfgNode(cfg_dict)

    # clear memory in GPU CUDA
    torch.cuda.empty_cache()

    model_fine = models.FlexibleNeRFModel(
        cfg.models.fine.num_layers,
        cfg.models.fine.hidden_size,
        cfg.models.fine.skip_connect_every,
        cfg.models.fine.num_encoding_fn_xyz,
        cfg.models.fine.num_encoding_fn_dir,
        model_type=model_type,
    )

    fine_model_secondary_list = []
    if model_type == 'ensemble':
        for i in range(cfg.experiment.num_models_secondary):
            model_fine_secondary = models.FlexibleNeRFModel(
                cfg.models_secondary.fine.num_layers,
                cfg.models_secondary.fine.hidden_size,
                cfg.models_secondary.fine.skip_connect_every,
                cfg.models_secondary.fine.num_encoding_fn_xyz,
                cfg.models_secondary.fine.num_encoding_fn_dir,
                model_type=model_type,
            )
            fine_model_secondary_list.append(model_fine_secondary)

    if os.path.exists(load_checkpoint):
        checkpoint = torch.load(load_checkpoint)
        model_fine.load_state_dict(checkpoint["model_fine_state_dict"])
        
        for i, fine_model_secondary in enumerate(fine_model_secondary_list):
            fine_model_secondary.load_state_dict(checkpoint["model_fine_secondary_state_dict"][i])
    else:
        sys.exit("Please enter the path of the checkpoint file.")
    
    model_fine.eval()
    if model_type == 'ensemble':
        for i in range(cfg.experiment.num_models_secondary):
            fine_model_secondary_list[i].eval()
    
    include_input_xyz = 3 if cfg.models.fine.include_input_xyz else 0
    include_input_dir = 3 if cfg.models.fine.include_input_dir else 0
    dim_xyz = include_input_xyz + 2 * 3 * cfg.models.fine.num_encoding_fn_xyz
    dim_dir = include_input_dir + 2 * 3 * cfg.models.fine.num_encoding_fn_dir
    if not cfg.models.fine.use_viewdirs:
        dim_dir = 0

    print('----------------------------------------')
    print("Scene: ", scene)
    print("Dataset: ", dataset)
    print("Iteration: ", iteration)
    print("Points per dimension: ", xyzNumPoint)

    dxyz = abs(xyzMax - xyzMin) / (xyzNumPoint - 1)

    voxelVol = vtkStructuredPoints()
    #voxelVol = vtkImageData()
    voxelVol.SetDimensions(xyzNumPoint, xyzNumPoint, xyzNumPoint)
    voxelVol.SetOrigin(-(abs(xyzMax-xyzMin)/2), -(abs(xyzMax-xyzMin)/2), -(abs(xyzMax-xyzMin)/2))
    # voxelVol.SetOrigin(-(abs(xyzMax-xyzMin)/2), -(abs(xyzMax-xyzMin)/2), 0.0)   # <===
    # voxelVol.SetOrigin(-(abs(xyzMax-xyzMin)/2), -(abs(xyzMax-xyzMin)/2), -0.5)   # <===
    voxelVol.SetSpacing(dxyz, dxyz, dxyz)

    #arrayColor = vtkDoubleArray()
    arrayColor = vtkFloatArray()
    arrayColor.SetNumberOfComponents(3) # this is 3 for a vector
    arrayColor.SetNumberOfTuples(voxelVol.GetNumberOfPoints())

    #arrayDensity = vtkDoubleArray()
    arrayDensity = vtkFloatArray()
    arrayDensity.SetNumberOfComponents(1) # this is 3 for a vector
    arrayDensity.SetNumberOfTuples(voxelVol.GetNumberOfPoints())

    
    tensor_input = torch.zeros(batch_size, dim_xyz+dim_dir)
    npoints = voxelVol.GetNumberOfPoints()
    
    with torch.no_grad():
        num_iterations = int(np.ceil(npoints / batch_size))
        
        output_point_color = []
        output_point_density = []
        output_point_uncertainty = []
        for i in tqdm(range(num_iterations)):
            indices = np.arange(i*batch_size, min((i+1)*batch_size, npoints))
            # print(f'{np.max(indices)}/{npoints}')
            
            xyzs = []
            for index in indices:
                x, y, z = voxelVol.GetPoint(index)
                xyzs.append([x,y,z])
            xyz_tensor = torch.Tensor(xyzs)
            encode_pos = helpers.embedding_encoding(xyz_tensor, num_encoding_functions=cfg.models.fine.num_encoding_fn_xyz)

            tensor_input = torch.zeros(len(indices), dim_xyz+dim_dir)
            tensor_input[..., : dim_xyz] = encode_pos

            if cfg.models.fine.use_viewdirs:
                encode_dir = helpers.embedding_encoding(xyz_tensor, num_encoding_functions=cfg.models.fine.num_encoding_fn_dir)
                # tensor_input[..., dim_xyz :] = encode_dir
                encode_dir_zeros = torch.zeros_like(encode_dir)
                tensor_input[..., dim_xyz :] = encode_dir_zeros
            
            output = model_fine(tensor_input) # [R, G, B, sigma] ###
            
            if model_type == 'ensemble':
                outputs_secondary = []
                for k in range(cfg.experiment.num_models_secondary):
                    output_secondary = fine_model_secondary_list[k](tensor_input)       # [R, G, B, sigma]
                    outputs_secondary.append(output_secondary)

            for j in range(output.shape[0]):
                point_colors = []
                point_densities = []

                sigma = torch.nn.functional.relu(output[j, 3])
                arrayDensity.SetValue(indices[j], sigma.cpu())
                color = torch.sigmoid(output[j, :3])

                point_colors.append(color)
                point_densities.append([sigma])

                if model_type == 'ensemble':
                    for k in range(len(outputs_secondary)):
                        output_secondary = outputs_secondary[k]
                        color = torch.sigmoid(output_secondary[j, :3])
                        point_colors.append(color)    # Append the RGB color from the secondary models into the list
                        sigma = torch.nn.functional.relu(output_secondary[j,3])
                        point_densities.append([sigma])    # Append the density from the secondary models into the list
                else:
                    uncertainty = torch.nn.functional.relu(output[j, 4])
                    output_point_uncertainty.append(uncertainty)

                output_point_color.append(point_colors)
                output_point_density.append(point_densities)

        output_point_color = np.array(output_point_color)
        output_point_density = np.array(output_point_density)
        
        if model_type == 'ensemble':
            uncertainties_color = []
            uncertainties_density = []
            for i in range(output_point_color.shape[0]):
                point_colors = output_point_color[i]
                point_densities = output_point_density[i]

                avg_distance_color = np.mean(pdist(point_colors, metric='euclidean'))
                uncertainties_color.append(avg_distance_color)

                avg_distance_density = np.mean(pdist(point_densities, metric='euclidean'))
                uncertainties_density.append(avg_distance_density)
        
        final_sigma = torch.Tensor(output_point_density[:,0])
        final_alpha = 1.0 - torch.exp(-final_sigma)
        alpha = numpy_support.numpy_to_vtk(num_array=final_alpha.numpy(), deep=True)

        voxelVolOpacity = vtkStructuredPoints()
        voxelVolOpacity.DeepCopy(voxelVol)
        voxelVolOpacity.GetPointData().SetScalars(alpha)

        store_path = f'datasets/{scene}/{model_type}/{dataset}/'

        writerOpacity = vtkStructuredPointsWriter()
        writerOpacity.WriteExtentOn()
        writerOpacity.SetFileName(store_path + "{}_{}_{}_opacity.vtk".format(scene, dataset, iteration))
        writerOpacity.SetInputData(voxelVolOpacity)
        writerOpacity.Write()

        if model_type == 'ensemble':
            # ### === Generate VTK file for RGB color uncertainty === ###
            uncertaintyColor_np = np.array(uncertainties_color)

            uncertaintyColor_np_normalize = (uncertaintyColor_np - np.min(uncertaintyColor_np)) / (np.max(uncertaintyColor_np) - np.min(uncertaintyColor_np))
            arrayUncertaintyColor_vtk = numpy_support.numpy_to_vtk(num_array=uncertaintyColor_np_normalize, deep=True)

            voxelVolUncertaintyColor = vtkStructuredPoints()
            voxelVolUncertaintyColor.DeepCopy(voxelVol)
            voxelVolUncertaintyColor.GetPointData().SetScalars(arrayUncertaintyColor_vtk)

            writerUncertaintyColor = vtkStructuredPointsWriter()
            writerUncertaintyColor.WriteExtentOn()
            writerUncertaintyColor.SetFileName(store_path + "{}_{}_{}_uncertainty_color.vtk".format(scene, dataset, iteration))
            writerUncertaintyColor.SetInputData(voxelVolUncertaintyColor)
            writerUncertaintyColor.Write()

            ### === Generate VTK file for density uncertainty === ###
            uncertaintyDesnity_np = np.array(uncertainties_density)

            uncertaintyDesnity_np_normalize = (uncertaintyDesnity_np - np.min(uncertaintyDesnity_np)) / (np.max(uncertaintyDesnity_np) - np.min(uncertaintyDesnity_np))
            arrayUncertaintyDensity_vtk = numpy_support.numpy_to_vtk(num_array=uncertaintyDesnity_np_normalize, deep=True)

            voxelVolUncertaintyDensity = vtkStructuredPoints()
            voxelVolUncertaintyDensity.DeepCopy(voxelVol)
            voxelVolUncertaintyDensity.GetPointData().SetScalars(arrayUncertaintyDensity_vtk)

            writerUncertaintyDensity = vtkStructuredPointsWriter()
            writerUncertaintyDensity.WriteExtentOn()
            writerUncertaintyDensity.SetFileName(store_path + "{}_{}_{}_uncertainty_density.vtk".format(scene, dataset, iteration))
            writerUncertaintyDensity.SetInputData(voxelVolUncertaintyDensity)
            writerUncertaintyDensity.Write()
        else:
            output_point_uncertainty = np.array(output_point_uncertainty)
            output_point_uncertainty_normalize = (output_point_uncertainty - np.min(output_point_uncertainty)) / (np.max(output_point_uncertainty) - np.min(output_point_uncertainty))
            uncertainty = numpy_support.numpy_to_vtk(num_array=output_point_uncertainty_normalize, deep=True)

            voxel_vol_uncertainty = vtkStructuredPoints()
            voxel_vol_uncertainty.DeepCopy(voxelVol)
            voxel_vol_uncertainty.GetPointData().SetScalars(uncertainty)

            writer_uncertainty = vtkStructuredPointsWriter()
            writer_uncertainty.WriteExtentOn()
            writer_uncertainty.SetFileName(store_path + "{}_{}_{}_uncertainty.vtk".format(scene, dataset, iteration))
            writer_uncertainty.SetInputData(voxel_vol_uncertainty)
            writer_uncertainty.Write()
