import vtk

class CustomPlaneWidget(vtk.vtkImagePlaneWidget):
    def __init__(self, mappers, interactors, z_buffer):
        super().__init__()

        self.mappers = mappers
        self.interactors = interactors
        self.z_buffer = z_buffer

        self.setup_plane(mappers[0])
        self.setup_widget(interactors[0])

        self.add_clipping_planes()
    
    def setup_plane(self, mapper):
        plane = vtk.vtkPlane()
        plane.SetOrigin(mapper.GetCenter())
        plane.SetNormal(1, 0, 0)
        self.plane = plane

    def setup_widget(self, interactor):
        self.SetInteractor(interactor)
        self.TextureVisibilityOff()
        self.UpdatePlacement()
        self.AddObserver('EndInteractionEvent', self.planeObserver)
        self.On()

    def add_clipping_planes(self):
        for mapper in self.mappers:
            mapper.AddClippingPlane(self.plane)
    
    def planeObserver(self, obj, event):
        plane = self.plane
        
        plane.SetOrigin(obj.GetCenter())
        plane.SetNormal(obj.GetNormal())

        self.z_buffer.update_buffer()
        for interactor in self.interactors:
            interactor.GetRenderWindow().Render()