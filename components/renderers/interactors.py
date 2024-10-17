from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
import numpy as np
import vtk.util.numpy_support as numpy_support
import copy
import os
import pdb
from matplotlib import cm

from .color_bar import ColorBar

colors = vtk.vtkNamedColors()

class CustomQVTKRenderWindowInteractor(QVTKRenderWindowInteractor):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.parent.resizeEvent = lambda event : self.resize_to_parent()
    
    def resize_to_parent(self):
        parent_size = self.parent.size()
        self.resize(parent_size.width(), parent_size.height())
        self.GetRenderWindow().SetSize(parent_size.width(), parent_size.height())
        self.update()

    def closeEvent(self, QCloseEvent):
        self.Finalize()
        super().closeEvent(QCloseEvent)

class CustomVolumeQVTKRenderWindowInteractor(CustomQVTKRenderWindowInteractor):
    def __init__(self, parent, title_txt):
        super().__init__(parent)
        self.renderer = None
        self.z_buffer = None

        self.set_interactor_style()
        self.set_title(title_txt)
        
        self.AddObserver('StartInteractionEvent', self.disable_z_buffer)
        self.AddObserver('EndInteractionEvent', self.update_z_buffer)

    def set_interactor_style(self):
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.SetInteractorStyle(style)

    def set_title(self, title_txt, font_path='./assets/Inter.ttf'):
        title = vtk.vtkTextActor()
        title.SetTextScaleModeToNone()
        
        if os.path.exists(font_path):
            title.GetTextProperty().SetFontFamily(vtk.VTK_FONT_FILE)
            title.GetTextProperty().SetFontFile(font_path)

        # title.GetTextProperty().SetFontFamilyToTimes()
        title.GetTextProperty().SetFontSize(14)
        title.GetTextProperty().SetColor(0.0, 0.0, 0.0)
        title.GetTextProperty().SetJustificationToCentered()
        title.SetPosition(150, 0)
        title.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        title.GetPositionCoordinate().SetValue(0.5, 0.9)
        title.SetInput(title_txt)

        self.title = title

    def disable_z_buffer(self, obj=None, key=None):
        self.z_buffer.disable_buffer()

    def update_z_buffer(self, obj=None, key=None):
        self.z_buffer.update_buffer()

    def set_camera_orientation(self, orientation):
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(orientation['position'])
        camera.SetFocalPoint(orientation['focal point'])
        camera.SetViewUp(orientation['view up'])
        camera.SetDistance(orientation['distance'])
        camera.SetClippingRange(orientation['clipping range'])
        self.camera = camera

    def set_camera(self, camera):
        self.renderer.SetActiveCamera(camera)
        self.renderer.ResetCamera()
        self.camera = camera

    def make_axes_actor(self):
        axes = vtk.vtkAxesActor()
        axes.SetShaftTypeToCylinder()
        axes.SetXAxisLabelText('X')
        axes.SetYAxisLabelText('Y')
        axes.SetZAxisLabelText('Z')
        axes.SetTotalLength(1.0, 1.0, 1.0)
        axes.SetCylinderRadius(0.5 * axes.GetCylinderRadius())
        axes.SetConeRadius(1.025 * axes.GetConeRadius())
        axes.SetSphereRadius(1.5 * axes.GetSphereRadius())
        self.axes = axes

        om1 = vtk.vtkOrientationMarkerWidget()
        om1.SetOrientationMarker(self.axes)
        # Position lower left in the viewport.
        om1.SetViewport(0, 0, 0.2, 0.2)
        om1.SetInteractor(self)
        om1.EnabledOn()
        om1.InteractiveOn()
        self.axes_widget = om1

class IsoSurfaceWindow(CustomVolumeQVTKRenderWindowInteractor):
    def __init__(self, parent, volume, filter_value, z_buffer, camera):
        super().__init__(parent, 'Isosurface')

        self.volume = volume
        self.filter_value = filter_value
        self.z_buffer = z_buffer

        self.setup()
        self.make_axes_actor()

        self.z_buffer.set_iso_renderer(self.renderer)

        camera.isosurface_window = self
        self.set_camera(camera)

        # self.render_axes()
        self.GetRenderWindow().Render()
    
    def setup(self):
        self.contour = self.setup_contour()
        self.mapper = self.setup_poly_mapper()
        self.actor = self.setup_actor()
        self.renderer = self.setup_renderer()

    def setup_contour(self):
        contour = vtk.vtkContourFilter()
        contour.SetInputData(self.volume)
        contour.SetValue(0, self.filter_value)
        return contour
    
    def setup_poly_mapper(self):
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.contour.GetOutputPort())
        mapper.ScalarVisibilityOff()
        return mapper
    
    def setup_actor(self):
        actor = vtk.vtkActor()
    
        actor.SetMapper(self.mapper)
        #actor.GetProperty().SetColor(colors.GetColor3d('green'))

        purple_color = np.array([212,185,218]) / 255
        actor.GetProperty().SetColor(purple_color[0], purple_color[1], purple_color[2])

        actor.SetVisibility(True)
        return actor
    
    def setup_renderer(self):
        renderer = vtk.vtkRenderer()

        renderer.AddVolume(self.title)
        renderer.AddVolume(self.actor)

        renderer.SetBackground(colors.GetColor3d('white'))

        self.GetRenderWindow().AddRenderer(renderer)

        return renderer

class UncertaintyVolWindow(CustomVolumeQVTKRenderWindowInteractor):
    def __init__(self, parent, density_reader, uncertainty_reader, z_buffer, camera, name='Uncertainty'):
        super().__init__(parent, name)

        self.name = name
        self.density_reader = density_reader
        self.uncertainty_reader = uncertainty_reader
        self.z_buffer = z_buffer

        self.setup_density_volume()
        self.setup_uncertainty_volume()
        self.setup_colorbar()
        self.setup_renderer()
        self.make_axes_actor()

        self.z_buffer.add_renderer(self.renderer)

        camera.uncertainty_window = self
        self.set_camera(camera)

        self.GetRenderWindow().Render()

    def setup_density_volume(self):
        opacity_tf, color_tf = self.setup_density_tfs()
        volume_property = self.setup_volume_property(opacity_tf, color_tf)
        self.density_mapper = self.setup_mapper(self.density_reader)
        self.density_volume = self.setup_volume(volume_property, self.density_mapper)

    def setup_uncertainty_volume(self):
        opacity_tf, color_tf = self.setup_uncertainty_tfs()
        volume_property = self.setup_volume_property(opacity_tf, color_tf)
        self.uncertainty_mapper = self.setup_mapper(self.uncertainty_reader)
        self.uncertainty_volume = self.setup_volume(volume_property, self.uncertainty_mapper)

        self.uncertainty_scalars = self.uncertainty_reader.GetOutput().GetPointData().GetScalars()

    def setup_volume(self, volume_property, volume_mapper):
        volume = vtk.vtkVolume()
        volume.SetMapper(volume_mapper)
        volume.SetProperty(volume_property)
        return volume

    def setup_uncertainty_tfs(self):
        is_color_unc_tf = 'color' in self.name.lower()

        opacity_tf = vtk.vtkPiecewiseFunction()
        opacity_tf.AddPoint(0, 0)
        opacity_tf.AddPoint(0.25, 1)
        self.uncertainty_opacity_tf = opacity_tf

        color_tf = vtk.vtkColorTransferFunction()
        if is_color_unc_tf:
            custom_cmap = cm.get_cmap('viridis', 100)
        else:
            custom_cmap = cm.get_cmap('inferno', 100)
        color_tf.AddRGBPoint(0.00, 1.0, 1.0, 1.0)
        max_val = np.array(custom_cmap(0.5))[:3]
        color_tf.AddRGBPoint(1, max_val[0], max_val[1], max_val[2])

        self.uncertainty_color_tf = color_tf

        return opacity_tf, color_tf

    def setup_density_tfs(self):
        opacity_tf = vtk.vtkPiecewiseFunction()
        opacity_tf.AddPoint(0, 0)
        opacity_tf.AddPoint(0.6, 1)
        opacity_tf.AddPoint(1, 0.99)

        self.density_opacity_tf = opacity_tf

        color_tf = vtk.vtkColorTransferFunction()
        color_tf.AddRGBPoint(0.00, 0.0, 0.0, 0.0)
        color_tf.AddRGBPoint(1.00, 1.0, 1.0, 1.0)
        
        self.density_color_tf = color_tf

        return opacity_tf, color_tf

    def setup_volume_property(self, opacity_tf, color_tf):
        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(color_tf)
        volume_property.SetScalarOpacity(opacity_tf)
        volume_property.ShadeOn()
        volume_property.SetInterpolationTypeToLinear()

        return volume_property

    def setup_mapper(self, data_reader):
        volume_mapper = vtk.vtkOpenGLGPUVolumeRayCastMapper()
        volume_mapper.SetInputConnection(data_reader.GetOutputPort())
        return volume_mapper
    
    def setup_colorbar(self):
        self.colorbar = ColorBar(title=self.name, values=self.uncertainty_color_tf, interactor=self)

    def setup_renderer(self):
        renderer = vtk.vtkRenderer()

        renderer.AddVolume(self.density_volume)
        renderer.AddVolume(self.uncertainty_volume)
        renderer.AddVolume(self.colorbar.actor)
        renderer.AddVolume(self.title)
        renderer.SetBackground(colors.GetColor3d('white'))

        self.renderer = renderer

        # self.renderer = renderer
        self.GetRenderWindow().AddRenderer(renderer)

    def update_tf(self):
        self.density_volume.GetProperty().SetScalarOpacity(self.density_opacity_tf)
        self.uncertainty_volume.GetProperty().SetScalarOpacity(self.uncertainty_opacity_tf)
        self.GetRenderWindow().Render()

    def set_selected_alpha(self, selected_inds):
        uncertainty_reader_data = self.uncertainty_reader.GetOutput()

        original_scalars = numpy_support.vtk_to_numpy(self.uncertainty_scalars)
        scalar_inds = np.arange(original_scalars.shape[0])

        new_scalars = copy.deepcopy(original_scalars)
        unselected_inds = np.setdiff1d(scalar_inds, selected_inds)
        new_scalars[unselected_inds] = 0

        new_scalars_vtk = numpy_support.numpy_to_vtk(num_array=new_scalars, deep=True)
        uncertainty_reader_data.GetPointData().SetScalars(new_scalars_vtk)
        self.uncertainty_reader.SetOutput(uncertainty_reader_data)
        self.update_z_buffer()

    def reset_alphas(self):
        self.uncertainty_reader.GetOutput().GetPointData().SetScalars(self.uncertainty_scalars)
        self.update_z_buffer()