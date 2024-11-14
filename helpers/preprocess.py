import vtk
import numpy as np
import pdb
import matplotlib.pyplot as plt

from helpers.vtk import range_lower_than_90

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

def compute_means_stddevs(theta_range, phi_range, orig_orientation, camera, iso_renderer, density_renderer, color_renderer, model_type):
    means_color = np.zeros((theta_range.shape[0], phi_range.shape[0]))
    standard_deviations_color = np.zeros((theta_range.shape[0], phi_range.shape[0]))

    means_density = np.zeros((theta_range.shape[0], phi_range.shape[0]))
    standard_deviations_density = np.zeros((theta_range.shape[0], phi_range.shape[0]))

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

            # if int(theta) == 0 and (int(phi) > 90 or int(phi) < -90):
            #     pdb.set_trace()

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

            # plt.imsave(f'iso/{new_theta}-{new_phi}-{np.around(azimuth, 2)}-{np.around(elevation, 2)}.png', iso_image_filter)
            # pdb.set_trace()

            density_image_filter = get_image_filter(density_renderer.GetRenderWindow())
            density_image_occupied = density_image_filter[occupied_pixel_ids]
            # if model_type == 'ensemble':
            #     # density_image_occupied = density_image_filter
            #     density_image_occupied = density_image_filter[occupied_pixel_ids]
            # else:
            #     density_image_occupied = density_image_filter

            density_image_filter = np.rot90(density_image_filter, k=1)

            # compute histogram
            # plt.hist(density_image_filter.flatten()[np.argwhere(density_image_filter.flatten() > 0.05)], bins=30)
            # plt.ylabel('Frequency')
            # plt.xlabel('Data')
            # plt.savefig(f'density/{new_theta}-{new_phi}-hist.png')
            # plt.close()
            # pdb.set_trace()

            # plt.imsave(f'density/{new_theta}-{new_phi}.png', density_image_filter)
            means_density[i, j] = np.mean(density_image_occupied)

            # density_image_occupied[density_image_occupied > 0] = 1
            standard_deviations_density[i, j] = np.std(density_image_occupied)

            if model_type == 'ensemble':
                color_image_filter = get_image_filter(color_renderer.GetRenderWindow())
                # color_image_occupied = color_image_filter
                color_image_occupied = color_image_filter[occupied_pixel_ids]
                means_color[i, j] = np.mean(color_image_occupied)

                # color_image_occupied[color_image_occupied > 0] = 1
                standard_deviations_color[i, j] = np.std(color_image_occupied)

            heatmap_angles[i, j] = f'{int(new_theta)}-{int(new_phi)}'

    return means_color, standard_deviations_color, means_density, standard_deviations_density, heatmap_angles
    
            