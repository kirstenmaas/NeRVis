import vtk
import numpy as np
import pdb

class CustomCamera(vtk.vtkCamera):
    def __init__(self):
        super().__init__()

        self.azimuth = None
        self.elevation = None

        self.set_original_orientation()
        self.setup()

    def set_original_orientation(self):
        orientation = dict()
        orientation['position'] = self.GetPosition()
        orientation['focal point'] = self.GetFocalPoint()
        orientation['view up'] = self.GetViewUp()
        orientation['distance'] = self.GetDistance()
        orientation['clipping range'] = self.GetClippingRange()
        orientation['orientation'] = self.GetOrientation()
        self.orientation = orientation

    def setup(self):
        self.Zoom(5.0)
        self.Dolly(0.2)

    def update_angles(self, azimuth, elevation):
        # make sure we only update if new values arrive
        if self.azimuth != azimuth or self.elevation != elevation:
            self.isosurface_window.set_camera_orientation(self.orientation)
            self.uncertainty_window.set_camera_orientation(self.orientation)

            self.set_angles(azimuth, elevation)
            self.isosurface_window.renderer.ResetCamera()

            self.OrthogonalizeViewUp()
            
            self.uncertainty_window.renderer.SetActiveCamera(self)
            self.uncertainty_window.renderer.ResetCamera()

            self.isosurface_window.update_z_buffer()
            self.uncertainty_window.update_z_buffer()

    def set_angles(self, azimuth, elevation):
        self.azimuth = azimuth
        self.elevation = elevation

        self.Azimuth(azimuth)
        self.Elevation(elevation)