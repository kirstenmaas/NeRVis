import vtk
import numpy as np

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

    def update_angles(self, theta, phi):
        # make sure we only update if new values arrive
        if self.azimuth != theta or self.elevation != phi:
            self.isosurface_window.set_camera_orientation(self.orientation)
            self.uncertainty_window.set_camera_orientation(self.orientation)

            self.set_angles(theta, phi)
            self.isosurface_window.renderer.ResetCamera()
            
            self.uncertainty_window.renderer.SetActiveCamera(self)
            self.uncertainty_window.renderer.ResetCamera()
            self.set_new_view_up()

            self.isosurface_window.update_z_buffer()
            self.uncertainty_window.update_z_buffer()

    def set_angles(self, theta, phi):
        self.azimuth = theta
        self.elevation = phi
        
        if int(np.abs(phi)) == 90:
            # set angle to 85 to avoid parallel view plane
            sign = phi/90
            phi = sign * (np.abs(phi) - 5)

        self.Azimuth(theta)
        self.Elevation(phi)

    def set_new_view_up(self):
        view_up_vector = self.GetViewUp()
        view_plane_normal = self.GetViewPlaneNormal()

        angle, cos_similarity = self.similarity_vectors(view_up_vector, view_plane_normal)
        if abs(cos_similarity) > 0.998:
            self.SetViewUp(0.0, 0.0, 1.0)
        else:
            self.SetViewUp(0.0, 1.0, 0.0)

    def similarity_vectors(self, vector1, vector2):
        """
        Calculate the angle in degrees between two vectors.

        Parameters:
        -----------
        vector1 : numpy.ndarray
            The first vector.
        vector2 : numpy.ndarray
            The second vector.

        Returns:
        --------
        angle : float
            The angle in degrees between the two vectors.
        cos_similarity : float
            The cosine similarity between the two vectors.
        """
        dot_product = np.dot(vector1, vector2)
        norm_vector1 = np.linalg.norm(vector1)
        norm_vector2 = np.linalg.norm(vector2)
        cos_similarity = dot_product / (norm_vector1 * norm_vector2)

        # Calculate the angle in degrees
        angle = np.arccos(cos_similarity) * 180.0 / np.pi

        return angle, cos_similarity