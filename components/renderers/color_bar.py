import vtk
import os

class ColorBar(vtk.vtkScalarBarWidget):
    def __init__(self, title, values, interactor):
        super(vtk.vtkScalarBarWidget, self).__init__()

        self.title = title
        self.values = values
        self.interactor = interactor

        self.setup_actor()
        self.assign_actor()

    def setup_actor(self, font_path='./assets/Inter.ttf'):
        actor = vtk.vtkScalarBarActor()
        actor.SetOrientationToHorizontal()
        actor.SetLookupTable(self.values)
        actor.SetWidth(0.1)
        actor.SetHeight(0.75)
        actor.SetUnconstrainedFontSize(True)
        actor.SetTitle('Uncertainty') #self.title

        # colorbar axis labels
        label_format = vtk.vtkTextProperty()
        label_format.SetColor(0, 0, 0)
        if os.path.exists(font_path):
            label_format.SetFontFamily(vtk.VTK_FONT_FILE)
            label_format.SetFontFile(font_path)
        actor.SetLabelTextProperty(label_format)

        title_format = vtk.vtkTextProperty()
        title_format.SetColor(0, 0, 0)
        title_format.SetFontSize(10)
        if os.path.exists(font_path):
            title_format.SetFontFamily(vtk.VTK_FONT_FILE)
            title_format.SetFontFile(font_path)
        actor.SetTitleTextProperty(title_format)

        self.actor = actor

    def assign_actor(self):
        self.SetInteractor(self.interactor)
        self.SetScalarBarActor(self.actor)
        self.On()
