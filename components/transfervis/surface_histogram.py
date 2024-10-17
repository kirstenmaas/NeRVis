import vtk
import os

from ..renderers.interactors import CustomQVTKRenderWindowInteractor

class SurfaceHistogram(CustomQVTKRenderWindowInteractor):
    def __init__(self, parent, title, x_axis_label, y_axis_label, data, iso_surface_boundary):
        super().__init__(parent)

        self.title = title
        self.x_axis_label = x_axis_label
        self.y_axis_label = y_axis_label
        self.data = data
        self.iso_surface_boundary = iso_surface_boundary

        self.boundary_line = None

        self.define_color()
        self.setup_view()
        self.setup_chart()
        self.setup_data_table()
        self.setup_data_chart()

        self.setup_chart_ticks()
        self.draw_boundary_line()
        self.render()
    
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
        # chart.GetTitleProperties().SetUseTightBoundingBox(False)
        chart.GetTitleProperties().SetLineOffset(0)
        chart.GetTitleProperties().SetJustificationToCentered()
        chart.GetTitleProperties().SetVerticalJustificationToCentered()
        self.set_font_property(chart.GetTitleProperties(), font_size=15)
        
        chart.GetAxis(0).SetTitle(self.y_axis_label)
        self.set_font_property(chart.GetAxis(0).GetLabelProperties(), font_size=14)
        self.set_font_property(chart.GetAxis(0).GetTitleProperties(), font_size=14)
        
        chart.GetAxis(1).SetTitle(self.x_axis_label)
        self.set_font_property(chart.GetAxis(1).GetLabelProperties(), font_size=14)
        self.set_font_property(chart.GetAxis(1).GetTitleProperties(), font_size=14)
        
        chart.ForceAxesToBoundsOn()
        
        self.chart = chart

        self.view.GetScene().AddItem(chart)

    def set_font_property(self, text_property, font_size=14, font_path='./assets/Inter.ttf'):
        text_property.SetFontSize(font_size)
        if os.path.exists(font_path):
            text_property.BoldOff()
            text_property.SetFontFamily(vtk.VTK_FONT_FILE)
            text_property.SetFontFile(font_path)

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

    def setup_chart_ticks(self, tick_positions=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]):
        x_tick_position = vtk.vtkDoubleArray()
        x_tick_label = vtk.vtkStringArray()
        for i, value in enumerate(tick_positions):
            x_tick_position.InsertNextValue(value)
            x_tick_label.InsertNextValue(str(value))
        
        xAxis = self.chart.GetAxis(vtk.vtkAxis.BOTTOM)
        xAxis.SetRange(0.0, 1.0)
        xAxis.SetCustomTickPositions(x_tick_position, x_tick_label)
        xAxis.SetMinimumLimit(0.0)
        xAxis.SetMaximumLimit(1.0)
        xAxis.RecalculateTickSpacing()

        yAxis = self.chart.GetAxis(vtk.vtkAxis.LEFT)
        yAxis.SetBehavior(vtk.vtkAxis.FIXED)

    def draw_boundary_line(self, show=True):
        self.create_empty_table()
        self.draw_table_values()
        if show:
            self.draw_vertical_line()
        else:
            self.draw_point()

        if not self.boundary_line:
            vertical_line = self.chart.AddPlot(vtk.vtkChart.LINE)
            vertical_line.SetInputData(self.table, 0, 1)
            vertical_line.SetColor(0.0, 1.0, 0.0)
            vertical_line.SetWidth(2)
            self.boundary_line = vertical_line
        else:
            self.boundary_line.SetInputData(self.table, 0, 1)

    def create_empty_table(self):
        table = vtk.vtkTable()
        
        index = vtk.vtkFloatArray()
        index.SetName("Index")
        table.AddColumn(index)

        value = vtk.vtkFloatArray()
        value.SetName("Value")
        table.AddColumn(value)

        self.table = table

    def draw_table_values(self):
        table = self.table
        
        table.SetNumberOfRows(2)
        table.SetValue(0, 0, self.iso_surface_boundary)
        table.SetValue(0, 1, 0.0)
        table.SetValue(1, 0, self.iso_surface_boundary)

        self.table = table

    def draw_vertical_line(self):
        self.table.SetValue(1, 1, 1.0)

    def draw_point(self):
        self.table.SetValue(1, 1, 0.0)

    def render(self):
        self.view.SetRenderWindow(self.GetRenderWindow())
        self.view.Render()