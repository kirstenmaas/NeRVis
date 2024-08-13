import vtk

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