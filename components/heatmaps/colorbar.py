from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from matplotlib import cm
from matplotlib.colors import ListedColormap

from .styles import colorbar_style

class Colorbar(QWidget):
    def __init__(self, parent, vmin, vmax, color_str, name):
        super().__init__()

        self.vmin = vmin
        self.vmax = vmax
        self.color_str = color_str

        self._main = QVBoxLayout(parent)

        label = QLabel(name)
        label.setWordWrap(True)
        label.setStyleSheet(colorbar_style)
        # label.setFixedHeight(50)
        # label.setFixedWidth(50)
        self._main.addWidget(label)

        self.setup_canvas()
        self.setup_figure()
        self.canvas.updateGeometry()

    def setup_canvas(self):
        plt.rcParams["font.family"] = "Inter"
        plt.rcParams["font.size"] = 8

        self.canvas = FigureCanvas(Figure(layout='constrained'))
        self._main.addWidget(self.canvas)
        self.canvas.draw()

    def setup_figure(self, num_ticks=5):
        plt.tight_layout()

        self.fig = self.canvas.figure

        self.ax = self.fig.subplots()
       
        cmap = self.get_cmap()

        norm = mpl.colors.Normalize(vmin=self.vmin, vmax=self.vmax)
        colorbar = self.fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
             cax=self.ax, orientation='vertical')
        colorbar.set_ticks([0, self.vmax])
        colorbar.set_ticklabels([0, np.around(self.vmax, 3)])
        
    def get_cmap(self):
        # blue
        # color_range = np.array([(255, 255, 255), (31,120,180)]) / 255
        cmap = cm.get_cmap('inferno', 100)
        if self.color_str == 'green':
            cmap = cm.get_cmap('viridis', 100)
        
        # shorten the range of the colors between [0.1, 0.9]
        cmap = ListedColormap(cmap(np.linspace(0.1, 0.9, num=100, endpoint=True)))

            # color_range = np.array([(255, 255, 255), (102,166,30)]) / 255
        # cmap = mpl.colors.LinearSegmentedColormap.from_list(self.color_str, color_range)
        return cmap
    
    def resizeEvent(self, event):
        self.canvas.updateGeometry()
        self.canvas.draw()