from PyQt6.QtWidgets import (
    QVBoxLayout,
    QRadioButton,
    QCheckBox
)

class SurfaceRadioButton(QVBoxLayout):
    def __init__(self, parent, uncertainty_windows):
        super().__init__(parent)

        self.checked = True

        self.parent = parent
        self.uncertainty_windows = uncertainty_windows

        self.setup_button()

    def setup_button(self):
        button = QCheckBox("Display isosurface")
        button.setStyleSheet("QCheckBox { font-family: Inter; font-size: 14px }")
        button.setChecked(self.checked)
        button.toggled.connect(self.on_click)

        self.button = button
        self.addWidget(button)

    def on_click(self):
        self.checked = self.button.isChecked()

        uncertainty_windows = self.uncertainty_windows

        for uncertainty_window in uncertainty_windows:
            if self.checked:
                uncertainty_window.renderer.AddVolume(uncertainty_window.density_volume)
                uncertainty_window.z_buffer.display_isosurface = True
            else:
                uncertainty_window.renderer.RemoveVolume(uncertainty_window.density_volume)
                uncertainty_window.z_buffer.display_isosurface = False
            uncertainty_window.update_z_buffer()
            
            uncertainty_window.renderer.GetRenderWindow().Render()