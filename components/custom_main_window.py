from PyQt6.QtWidgets import (
    QMainWindow,
)

class CustomMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(" QMainWindow { background-color: white; }")

        self.mpl_plots = []
        self.interactors = []
    
    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)

        for plot in self.mpl_plots:
            plot.resizeEvent(None)

    def set_mpl_plot(self, plt):
        mpl_plots = self.mpl_plots
        mpl_plots.append(plt)

        self.mpl_plots = mpl_plots

    def set_interactor(self, inter):
        interactors = self.interactors
        interactors.append(inter)

        self.interactors = interactors

    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)

        for interactor in self.interactors:
            interactor.Finalize()
            interactor.parent.close()
            

