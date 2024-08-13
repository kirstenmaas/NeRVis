import vtk

from ..renderers.interactors import CustomQVTKRenderWindowInteractor

class TransferFunction(CustomQVTKRenderWindowInteractor):
    def __init__(self, parent, title, x_axis_label, y_axis_label, color_tf, opacity_tf, data, volume_window):
        super().__init__(parent)
        
        self.title = title
        self.x_axis_label = x_axis_label
        self.y_axis_label = y_axis_label
        self.color_tf = color_tf
        self.opacity_tf = opacity_tf
        self.data = data
        self.volume_window = volume_window

        self.define_color()
        self.setup_view()
        self.setup_chart()
        self.setup_composite_function()
        self.setup_control_points()
        self.setup_data_table()
        self.setup_data_chart()

        self.view.SetRenderWindow(self.GetRenderWindow())
        self.view.Render()

    def define_color(self, alpha=10):
        color_series = vtk.vtkColorSeries()
        color_series.SetColorScheme(vtk.vtkColorSeries.BREWER_SEQUENTIAL_BLUE_GREEN_3)
        color = color_series.GetColor(0)
        
        self.color = vtk.vtkColor4ub(color.GetRed(), color.GetGreen(), color.GetBlue(), int(alpha))

    def setup_view(self):
        view = vtk.vtkContextView()
        view.GetRenderer().SetBackground(1.0, 1.0, 1.0)
        view.GetRenderWindow().SetMultiSamples(0)
        self.view = view

    def setup_chart(self):
        chart = vtk.vtkChartXY()
        chart.SetTitle(self.title)
        chart.GetAxis(0).SetTitle(self.y_axis_label)
        chart.GetAxis(1).SetTitle(self.x_axis_label)
        chart.ForceAxesToBoundsOn()
        chart.GetAxis(vtk.vtkAxis.LEFT).SetBehavior(vtk.vtkAxis.FIXED)
        self.chart = chart

        self.view.GetScene().AddItem(chart)

    def setup_composite_function(self):
        item = vtk.vtkCompositeTransferFunctionItem()
        item.SetColorTransferFunction(self.color_tf)
        item.SetOpacityFunction(self.opacity_tf)
        item.SetMaskAboveCurve(True)
        self.chart.AddPlot(item)

    def setup_control_points(self):
        control_points = vtk.vtkCompositeControlPointsItem()
        control_points.SetColorTransferFunction(self.color_tf)
        control_points.SetOpacityFunction(self.opacity_tf)

        self.chart.AddPlot(control_points)

        control_points.AddObserver(vtk.vtkCommand.EndEvent, self.updateTransferFunction)

    def setup_data_table(self):
        table = vtk.vtkTable()
        data = self.data

        arr_index = vtk.vtkFloatArray()
        arr_index.SetName("Index")
        table.AddColumn(arr_index)
        
        arr_value = vtk.vtkFloatArray()
        arr_value.SetName("Value")
        table.AddColumn(arr_value)

        table.SetNumberOfRows(len(data))
        num_row = len(data)
        for i in range(num_row):
            table.SetValue(i, 0, (i + 1)/num_row)
            table.SetValue(i, 1, data[i])

        self.data_table = table

    def setup_data_chart(self):
        color = self.color 

        line = self.chart.AddPlot(vtk.vtkChart.BAR)
        line.SetColor(color.GetRed(),
            color.GetGreen(),
            color.GetBlue(),
            color.GetAlpha())
        line.SetInputData(self.data_table, 0, 1)

    def updateTransferFunction(self, obj, event):
        self.volume_window.update_tf()
