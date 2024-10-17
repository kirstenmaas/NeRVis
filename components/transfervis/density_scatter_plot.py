from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path
import matplotlib.pyplot as plt
import matplotlib

from scipy import stats

from .styles import title_style

class DensityScatterPlot(QWidget):
    def __init__(self, parent, data, renderer_windows):
        super().__init__(parent)
        self.data = data
        self.renderer_windows = renderer_windows

        self.standard_alpha = 0.25
        self.unselected_alpha = 0.1
        self.selected_alpha = 1

        self.parent = parent
        self._main = QVBoxLayout(self.parent)

        # add title
        self.titleLabel = QLabel('2D Transfer Function')
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setStyleSheet(title_style)

        self._main.setContentsMargins(0,0,0,0)
        self._main.setSpacing(0)
        self._main.addWidget(self.titleLabel)

        self.setup_data()
        self.setup_canvas()
        self.setup_figure()

        
        # self.create_density_plot()
        self.setup_scatter_plot_interaction()

        self.canvas.updateGeometry()
        
    def setup_canvas(self, figsize=100):
        plt.rcParams["font.family"] = "Inter"
        self.canvas = FigureCanvas(Figure())

        self._main.addWidget(self.canvas)
        self.canvas.draw()
    
    def setup_figure(self):
        plt.tight_layout()
        self.fig = self.canvas.figure
        
        self.ax = self.fig.subplots()
        self.fig.subplots_adjust(left=0.2, bottom=0.15, right=0.95, top=0.95)
        
        self.ax.set_xlabel("Color uncertainty value")
        self.ax.set_xlim(0, 1)
        # self.ax.set_xbound(lower=np.min(self.color_data), upper=1)
        self.ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])

        self.ax.set_ylabel("Density uncertainty value")
        # print(np.min(self.density_data))
        self.ax.set_ylim(np.min(self.density_data), 1)
        # self.ax.set_ybound(lower=np.min(self.density_data), upper=1)
        self.ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])

    def setup_data(self):
        data = self.data

        self.color_data = data[:,0]
        self.density_data = data[:, 1]
        self.ind_data = data[:, 2]

    def create_density_plot(self, nbins=80):
        k = stats.gaussian_kde([self.color_data, self.density_data])
        xi, yi = np.mgrid[0.000:1.000:nbins*1j, 0.000:1.000:nbins*1j]
        zi = k(np.vstack([xi.flatten(), yi.flatten()]))

        color_range = np.array([(255, 255, 255), (217,71,1)]) / 255
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list('', color_range)

        self.density_plot = self.ax.pcolormesh(xi, yi, zi.reshape(xi.shape), shading='auto', cmap=cmap)
        self.fig.colorbar(self.density_plot)

    def setup_scatter_plot_interaction(self):
        self.selector = SelectFromCollection(self.ax, self.color_data, self.density_data, self.ind_data, self.renderer_windows, self.standard_alpha, self.selected_alpha, self.unselected_alpha)

    def resizeEvent(self, event):
        self.canvas.updateGeometry()
        self.canvas.draw()

class SelectFromCollection:
    def __init__(self, ax, color_data, density_data, ind_data, renderer_windows, standard_alpha=0.25, selected_alpha=1, unselected_alpha=0.2):
        self.ax = ax

        self.color_data = color_data
        self.density_data = density_data
        self.ind_data = ind_data

        self.renderer_windows = renderer_windows

        self.standard_alpha = standard_alpha
        self.selected_alpha = selected_alpha
        self.unselected_alpha = unselected_alpha

        self.standard_colors = np.tile([0, 0, 0, self.standard_alpha], (self.color_data.shape[0], 1))

        self.canvas = ax.figure.canvas
        self.scatter_plot = self.create_scatter_plot(self.color_data, self.density_data, self.standard_colors)

        self.xys = self.scatter_plot.get_offsets()
        self.Npts = len(self.xys)

        lassoprops = {'color': 'black', 'linewidth': 1, 'alpha': 0.8 }
        self.lasso = LassoSelector(self.ax, onselect=lambda verts: self.onselect(verts), props=lassoprops, useblit=True)

        self.inds = []
    
    def create_scatter_plot(self, color_data, density_data, colors):
        scatter_plot = self.ax.scatter(color_data, density_data, color=colors, s=20, edgecolor='none')
        return scatter_plot

    def onselect(self, verts):
        path = Path(verts)
        
        # find selected inds
        self.inds = np.nonzero(path.contains_points(self.xys))[0]

        # remove all the current scatter plots
        self.scatter_plot.remove()

        # plot the new points
        if len(self.inds) > 0:
            color_data = self.color_data
            density_data = self.density_data
            alpha_data = np.zeros((density_data.shape[0], 4))
            alpha_data[:, -1] = self.unselected_alpha

            # draw the selected points
            alpha_data[self.inds, -1] = self.selected_alpha

            print(self.unselected_alpha)

            scatter_plot = self.create_scatter_plot(color_data, density_data, alpha_data)
        else:
            scatter_plot = self.create_scatter_plot(self.color_data, self.density_data, self.standard_colors)

        self.scatter_plot = scatter_plot

        self.update_renderer_windows(self.inds)

        self.canvas.draw_idle()
    
    def update_renderer_windows(self, inds):
        
        for renderer_window in self.renderer_windows:
            if len(inds) > 0:
                renderer_window.set_selected_alpha(self.ind_data[inds].astype(int))
            else:
                renderer_window.reset_alphas()