import vtk
import pdb

class ZBuffer():
    def __init__(self):
        self.display_isosurface = True
        self.data = vtk.vtkFloatArray()

        self.iso_renderer = None
        self.renderers = []

    def set_iso_renderer(self, iso_renderer):
        self.iso_renderer = iso_renderer

    def add_renderer(self, renderer):
        renderers = self.renderers
        renderers.append(renderer)
        self.renderers = renderers

    def update_buffer(self):
        # self.disable_buffer()
        if self.display_isosurface:
            self.set_buffer()
            self.update_buffer_renderers()
        else:
            self.disable_buffer()

    def disable_buffer(self):
        for renderer in self.renderers:
            renderer.PreserveDepthBufferOff()
            renderer.GetRenderWindow().Render()

    def set_buffer(self):
        iso_renderer = self.iso_renderer

        iso_renderer.PreserveDepthBufferOff()
        iso_renderer.GetRenderWindow().Render()

        xmax, ymax = iso_renderer.GetRenderWindow().GetActualSize()
        iso_renderer.GetRenderWindow().GetZbufferData(0, 0, xmax-1, ymax-1, self.data)
        iso_renderer.GetRenderWindow().Render()
    
    def update_buffer_renderers(self):
        for renderer in self.renderers:
            renderer.PreserveDepthBufferOff()
            renderer.GetRenderWindow().Render()

            xmax, ymax = renderer.GetRenderWindow().GetActualSize()
            renderer.PreserveDepthBufferOn()
            renderer.GetRenderWindow().SetZbufferData(0, 0, xmax-1, ymax-1, self.data)
            renderer.GetRenderWindow().Render()