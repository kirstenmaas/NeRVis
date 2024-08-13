import vtk

class ColorBar(vtk.vtkScalarBarWidget):
    def __init__(self, title, values, interactor):
        super(vtk.vtkScalarBarWidget, self).__init__()

        self.title = title
        self.values = values
        self.interactor = interactor

        self.setup_actor()
        self.assign_actor()

    def setup_actor(self):
        actor = vtk.vtkScalarBarActor()
        actor.SetOrientationToHorizontal()
        actor.SetLookupTable(self.values)
        actor.SetWidth(0.1)
        actor.SetHeight(0.8)
        actor.SetUnconstrainedFontSize(True)
        actor.SetTitle(self.title)

        label_format = vtk.vtkTextProperty()
        label_format.SetColor(0, 0, 0)
        actor.SetLabelTextProperty(label_format)

        title_format = vtk.vtkTextProperty()
        title_format.SetColor(0, 0, 0)
        actor.SetTitleTextProperty(title_format)

        self.actor = actor

    def assign_actor(self):
        self.SetInteractor(self.interactor)
        self.SetScalarBarActor(self.actor)
        self.On()
