import vtk
import numpy as np
import pdb
import matplotlib.pyplot as plt
import vtk.util.numpy_support as numpy_support

import torch

from helpers.vtk import range_lower_than_90
from nerf import (
    get_ray_bundle,
)

def setup_isosurface(data):
    contour = vtk.vtkContourFilter()
    contour.SetInputData(data.opacity_volume)
    contour.SetValue(0, data.isosurface_filter_value)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(contour.GetOutputPort())
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    blue_color = np.array([8,104,172]) / 255
    actor.GetProperty().SetColor(blue_color[0], blue_color[1], blue_color[2])
    actor.SetVisibility(True)

    return contour, mapper, actor

def setup_uncertainty_volume(data_reader):
    opacity_tf, color_tf = setup_density_tfs()

    volume_property = vtk.vtkVolumeProperty()
    volume_property.SetColor(color_tf)
    volume_property.SetScalarOpacity(opacity_tf)
    volume_property.ShadeOn()
    volume_property.SetInterpolationTypeToLinear()

    volume_mapper = vtk.vtkOpenGLGPUVolumeRayCastMapper()
    volume_mapper.SetInputConnection(data_reader.GetOutputPort())

    volume = vtk.vtkVolume()
    volume.SetMapper(volume_mapper)
    volume.SetProperty(volume_property)
    return volume

def setup_density_tfs():
    opacity_tf = vtk.vtkPiecewiseFunction()
    opacity_tf.AddPoint(0, 0)
    opacity_tf.AddPoint(0.25, 1)

    color_tf = vtk.vtkColorTransferFunction()
    color_tf.AddRGBPoint(0.00, 1, 0.0, 0.0)
    color_tf.AddRGBPoint(1, 1, 0, 0)

    return opacity_tf, color_tf

def setup_renderer(volume, color='White'):
    colors = vtk.vtkNamedColors()

    interactor = vtk.vtkRenderWindowInteractor()
    render_window = vtk.vtkRenderWindow()
    renderer = vtk.vtkRenderer()

    render_window.AddRenderer(renderer)
    interactor.SetRenderWindow(render_window)

    renderer.AddVolume(volume)
    renderer.SetBackground(colors.GetColor3d(color))

    return renderer, render_window

def get_orientation(camera):
    p = dict()
    p['position'] = camera.GetPosition()
    p['focal point'] = camera.GetFocalPoint()
    p['view up'] = camera.GetViewUp()
    p['distance'] = camera.GetDistance()
    p['clipping range'] = camera.GetClippingRange()
    p['orientation'] = camera.GetOrientation()
    return p

def set_orientation(renderer, p):
    camera = renderer.GetActiveCamera()
    camera.SetPosition(p['position'])
    camera.SetFocalPoint(p['focal point'])
    camera.SetViewUp(p['view up'])
    camera.SetDistance(p['distance'])
    camera.SetClippingRange(p['clipping range'])
    renderer.SetActiveCamera(camera)

def set_z_buffers(z_buffer_data, renderers):
    for renderer in renderers:
        xmax_color, ymax_color = renderer.GetRenderWindow().GetActualSize()
        renderer.PreserveDepthBufferOn()
        renderer.GetRenderWindow().SetZbufferData(0, 0, ymax_color-1, xmax_color-1, z_buffer_data)

def set_camera_renderers(renderers, camera):
    for renderer in renderers:
        renderer.SetActiveCamera(camera)
        renderer.ResetCamera()

def turn_off_z_buffers(renderers):
    for renderer in renderers:
        renderer.PreserveDepthBufferOff()
        renderer.GetRenderWindow().Render()

def get_z_buffer(iso_renderer, z_buffer_data_isosurface):
    xmax_isosurface, ymax_isosurface = iso_renderer.GetRenderWindow().GetActualSize()
    iso_renderer.GetRenderWindow().GetZbufferData(0, 0, ymax_isosurface-1, xmax_isosurface-1, z_buffer_data_isosurface)
    return z_buffer_data_isosurface

def get_image_filter(render_window):
    window_to_image_filter = vtk.vtkWindowToImageFilter()
    window_to_image_filter.SetInput(render_window)
    window_to_image_filter.Update()

    image_data = window_to_image_filter.GetOutput()
    width, height, _ = image_data.GetDimensions()

    # Access pixel data
    arr_pixel_value = []
    for x in range(width):
        for y in range(height):
            # pixel_r = image_data.GetScalarComponentAsFloat(x, y, 0, 0)
            pixel_g = image_data.GetScalarComponentAsFloat(x, y, 0, 1)
            # pixel_b = image_data.GetScalarComponentAsFloat(x, y, 0, 2)
            arr_pixel_value.append(pixel_g)
    np_arr_pixel_value = np.array(arr_pixel_value)

    # invert as background is white
    np_arr_pixel_value = 255 - np.array(np_arr_pixel_value)
    pix_map = np_arr_pixel_value.reshape((width, height)) / 255

    return pix_map

def get_image_filter_custom(render_window):
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(render_window)
    w2i.Update()

    image_data = w2i.GetOutput()
    width, height, _ = image_data.GetDimensions()

    scalars = numpy_support.vtk_to_numpy(image_data.GetPointData().GetScalars())
    scalars = scalars.reshape(height, width, -1)
    gray = scalars[..., 0]  # R channel, scalar value encoded as gray
    return gray

def thetaphi_to_azel(theta, phi):
    sin_el = np.sin(phi) * np.sin(theta)
    tan_az = np.cos(phi) * np.tan(theta)
    el = np.arcsin(sin_el)
    az = np.arctan(tan_az)

    el = np.rad2deg(el)
    az = np.rad2deg(az)
    
    return az, el

def convert_angle_to_range(angle):
    if angle > 180:
        angle = -(360 - angle)
    return angle

def compute_custom_maximums(camera, data, num_x, num_y, type='color', original_distance=3.0, step_size=0.01, dimension=128):
    if type == 'color':
        volume_array = data.uncertainty_volume_color.GetPointData().GetScalars()
    else:
        volume_array = data.uncertainty_volume.GetPointData().GetScalars()
    volume_array = numpy_support.vtk_to_numpy(volume_array).reshape((dimension, dimension, dimension))

    density_array = data.opacity_volume.GetPointData().GetScalars()
    density_array = numpy_support.vtk_to_numpy(density_array).reshape((dimension, dimension, dimension))

    mvt_matrix = camera.GetModelViewTransformMatrix()

    rotation_matrix = np.eye(4)
    for row in range(3):
        for col in range(3):
            rotation_matrix[row, col] = mvt_matrix.GetElement(row, col)

    # Get the camera position and focal point
    camera_pos = camera.GetPosition()
    focal_point = camera.GetFocalPoint()

    # Calculate the vector between camera and focal point
    vector = np.array([camera_pos[i] - focal_point[i] for i in range(3)])
    vector_magnitude = np.linalg.norm(vector)

    focal_length = original_distance / camera.GetDistance() * (1200)

    def rotate_by_phi_along_x(phi):
        tform = np.eye(4).astype(np.float32)
        tform[1, 1] = tform[2, 2] = np.cos(phi)
        tform[1, 2] = -np.sin(phi)
        tform[2, 1] = -tform[1, 2]
        return tform

    translationMatrix = np.eye(4).astype(np.float32)
    translationMatrix[2, 3] = 4.0 if vector_magnitude >= 4.0 else vector_magnitude
    rotationMatrix = np.linalg.inv(rotation_matrix)
    tranformationMatrix = rotate_by_phi_along_x(-90 / 180.0 * np.pi) @ np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]) @ rotationMatrix @ translationMatrix

    device = torch.device('cuda:0')

    render_poses = torch.stack([torch.from_numpy(tranformationMatrix)], 0).to(device)
    pose = render_poses.float()[0, :3, :4]
    volume_array = torch.from_numpy(volume_array).float().to(device)
    density_array = torch.from_numpy(density_array).float().to(device)

    hwf = [num_x, num_y, focal_length]

    ray_origins, ray_directions = get_ray_bundle(hwf[0], hwf[1], hwf[2], pose)
    
    ray_origins = ray_origins.reshape(num_y, num_x, 3)
    ray_dirs = ray_directions.reshape(num_y, num_x, 3)
    image_max = torch.zeros((num_y, num_x))


    H,W = ray_origins.shape[:2]
    Z,Y,X = volume_array.shape
    xmin, xmax, ymin, ymax, zmin, zmax = data.uncertainty_volume.GetBounds()
    def world_to_voxel(points):
        # points in [-1,1] -> voxel indices [0,dim-1]
        scaled = torch.zeros_like(points)
        scaled[:,0] = (points[:,0]-xmin)/(xmax-xmin)*(X-1)
        scaled[:,1] = (points[:,1]-ymin)/(ymax-ymin)*(Y-1)
        scaled[:,2] = (points[:,2]-zmin)/(zmax-zmin)*(Z-1)
        return scaled

    # March rays
    near = 2.0
    far = 5.0
    num_steps = int(np.ceil((far - near) / step_size))

    t_vals = near + torch.arange(0, num_steps).float().to(device) * step_size  # [num_steps]
    t_vals_exp = t_vals[None,None,:,None]  # (1,1,S,1)
    ray_dirs_exp = ray_dirs[:,:,None,:]    # (H,W,1,3)
    ray_origins_exp = ray_origins[:,:,None,:]  # (H,W,1,3)
    points = ray_origins_exp + t_vals_exp * ray_dirs_exp  # (H,W,S,3)
    points_flat = points.reshape(-1,3)
    voxel_pos_flat = world_to_voxel(points_flat)
    ix = torch.clip(voxel_pos_flat[:,0].int(), 0, X-1)
    iy = torch.clip(voxel_pos_flat[:,1].int(), 0, Y-1)
    iz = torch.clip(voxel_pos_flat[:,2].int(), 0, Z-1)

    sigma_flat = density_array[iz, iy, ix].reshape(H, W, num_steps)
    alpha = 1 - torch.exp(-sigma_flat * step_size)
    T = torch.cumprod(1 - alpha + 1e-10, dim=-1)
    T = torch.roll(T, shifts=1, dims=-1)
    T[:,:,0] = 1.0
    weights = alpha * T  # (H,W,S)
    mask = weights > 1e-8
    
    sampled_vals = volume_array[iz, iy, ix].reshape(H,W,num_steps)
    sampled_vals = torch.where(mask, sampled_vals, 0)
    
    image_max = torch.sum(sampled_vals, dim=-1)
    image_max = image_max.cpu().numpy()
    return np.max(image_max)

def compute_means_stddevs(theta_range, phi_range, orig_orientation, camera, iso_renderer, density_renderer, color_renderer, model_type, data):
    means_color = np.zeros((theta_range.shape[0], phi_range.shape[0]))
    standard_deviations_color = np.zeros((theta_range.shape[0], phi_range.shape[0]))
    maximum_color = np.zeros((theta_range.shape[0], phi_range.shape[0]))

    means_density = np.zeros((theta_range.shape[0], phi_range.shape[0]))
    standard_deviations_density = np.zeros((theta_range.shape[0], phi_range.shape[0]))
    maximum_density = np.zeros((theta_range.shape[0], phi_range.shape[0]))

    heatmap_angles = np.zeros((theta_range.shape[0], phi_range.shape[0])).astype('str')

    z_buffer_data_isosurface = vtk.vtkFloatArray()
    z_buffer_data_color_uncertainty = vtk.vtkFloatArray()
    z_buffer_data_density_uncertainty = vtk.vtkFloatArray()

    renderers = [iso_renderer, density_renderer]
    if model_type == 'ensemble':
        renderers.append(color_renderer)

    bottom_range_thetas = np.arange(-90, 91, 15).astype('int')
    bottom_range_phi = np.array([convert_angle_to_range(phi) for phi in np.arange(-90, 91, 15) + 180]).astype('int')

    for i, theta in enumerate(theta_range):
        for j, phi in enumerate(phi_range):
            # set original orientations
            for renderer in renderers:
                set_orientation(renderer, orig_orientation)

            new_theta = range_lower_than_90(theta)
            new_phi = range_lower_than_90(phi)

            azimuth, elevation = thetaphi_to_azel(np.deg2rad(new_theta), np.deg2rad(new_phi))

            if int(theta) in bottom_range_thetas and int(phi) in bottom_range_phi:
                elevation += 180

            if int(theta) == 0:
                elevation = int(range_lower_than_90(phi))
                
            # set angles
            camera.Azimuth(azimuth)
            camera.Elevation(elevation)

            iso_renderer.ResetCamera()
            camera.OrthogonalizeViewUp()

            set_camera_renderers(renderers, camera)
            turn_off_z_buffers(renderers)

            xmax_isosurface, ymax_isosurface = iso_renderer.GetRenderWindow().GetActualSize()
            iso_renderer.GetRenderWindow().GetZbufferData(0, 0, ymax_isosurface-1, xmax_isosurface-1, z_buffer_data_isosurface)
            
            xmax_color, ymax_color = density_renderer.GetRenderWindow().GetActualSize()
            density_renderer.PreserveDepthBufferOn()
            density_renderer.GetRenderWindow().GetZbufferData(0, 0, ymax_color-1, xmax_color-1, z_buffer_data_density_uncertainty)
            density_renderer.GetRenderWindow().SetZbufferData(0, 0, ymax_color-1, xmax_color-1, z_buffer_data_isosurface)
            
            if model_type == 'ensemble':
                xmax_color, ymax_color = color_renderer.GetRenderWindow().GetActualSize()
                color_renderer.PreserveDepthBufferOn()
                color_renderer.GetRenderWindow().GetZbufferData(0, 0, ymax_color-1, xmax_color-1, z_buffer_data_color_uncertainty)
                color_renderer.GetRenderWindow().SetZbufferData(0, 0, ymax_color-1, xmax_color-1, z_buffer_data_isosurface)
            
            iso_renderer.GetRenderWindow().Render()
            density_renderer.GetRenderWindow().Render()

            if model_type == 'ensemble':
                color_renderer.GetRenderWindow().Render()

            # from every angle, only consider the pixels of the object itself (based on isosurface)
            iso_image_filter = get_image_filter(iso_renderer.GetRenderWindow())
            occupied_pixel_ids = np.argwhere(iso_image_filter > 0)

            iso_image_filter = np.rot90(iso_image_filter, k=1)

            density_image_filter = get_image_filter(density_renderer.GetRenderWindow())
            density_image_occupied = density_image_filter[occupied_pixel_ids]

            density_image_filter = np.rot90(density_image_filter, k=1)

            means_density[i, j] = np.mean(density_image_occupied)
            standard_deviations_density[i, j] = np.std(density_image_occupied)

            maximum_density[i, j] = compute_custom_maximums(camera, data, xmax_color, ymax_color, type='density')

            if model_type == 'ensemble':
                color_image_filter = get_image_filter(color_renderer.GetRenderWindow())
                # color_image_occupied = color_image_filter
                color_image_occupied = color_image_filter[occupied_pixel_ids]
                means_color[i, j] = np.mean(color_image_occupied)

                # color_image_occupied[color_image_occupied > 0] = 1
                standard_deviations_color[i, j] = np.std(color_image_occupied)

                maximum_color[i, j] = compute_custom_maximums(camera, data, xmax_color, ymax_color, type='color')

            heatmap_angles[i, j] = f'{int(new_theta)}-{int(new_phi)}'

    return means_color, standard_deviations_color, maximum_color, means_density, standard_deviations_density, maximum_density, heatmap_angles
    
            