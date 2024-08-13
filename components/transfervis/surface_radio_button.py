from PyQt6.QtWidgets import (
    QVBoxLayout,
    QRadioButton
)

class SurfaceRadioButton(QVBoxLayout):
    def __init__(self, parent, surface_histogram, uncertainty_window):
        super().__init__(parent)

        self.checked = True

        self.parent = parent
        self.surface_histogram = surface_histogram
        self.uncertainty_window = uncertainty_window

        self.setup_button()

    def setup_button(self):
        button = QRadioButton("Display isosurface")
        button.setChecked(self.checked)
        button.toggled.connect(self.on_click)

        self.button = button
        self.addWidget(button)

    def on_click(self):
        self.checked = self.button.isChecked()

        surface_histogram = self.surface_histogram
        uncertainty_window = self.uncertainty_window

        surface_histogram.draw_boundary_line(show=self.checked)
        # surface_histogram.boundary_line.SetInputData(surface_histogram.table, 0, 1)

        if self.checked:
            uncertainty_window.renderer.AddVolume(uncertainty_window.density_volume)
            uncertainty_window.z_buffer.display_isosurface = True
        else:
            uncertainty_window.renderer.RemoveVolume(uncertainty_window.density_volume)
            uncertainty_window.z_buffer.display_isosurface = False
        uncertainty_window.update_z_buffer()
        
        # surface_histogram.GetRenderWindow().Render()
        uncertainty_window.renderer.GetRenderWindow().Render()