import vtk
import numpy as np

def read_volume_from_vtk_file(file_name):
    reader = vtk.vtkStructuredPointsReader()
    reader.SetFileName(file_name)
    reader.Update()
    volume = reader.GetOutput()
    return volume, reader

def resize_vtk_render_window(frame, interactor):
    size = frame.size()
    interactor.resize(size.width(), size.height())
    interactor.GetRenderWindow().SetSize(size.width(), size.height())
    interactor.update()

def range_lower_than_90(angle):
    # set angle to +-85 to avoid parallel view plane
    if int(np.abs(angle)) == 90:
        sign = angle/90
        angle = sign * (np.abs(angle) - 5)
    return angle