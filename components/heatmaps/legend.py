from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget, QGraphicsScene, QGraphicsEllipseItem, QGraphicsView, QGraphicsTextItem, QGraphicsRectItem
from PyQt6.QtGui import QColor, QFont

class Legend(QHBoxLayout):
    def __init__(self, parent):
        super().__init__(parent)

        self.setContentsMargins(10, 0, 0, 0)

        self.draw_training_point()
        self.draw_stddev_box('Low standard deviation', 0.4)
        self.draw_stddev_box('High standard deviation', 0.6)

    def draw_training_point(self, color=[125, 125, 125, 255]):
        training_point_widget = QWidget()
        training_point_widget.setFixedWidth(150)
        # training_point_widget.setStyleSheet(" QWidget { border: 1px solid black }")

        self.addWidget(training_point_widget)

        training_point_layout = QHBoxLayout(training_point_widget)
        training_point_layout.setContentsMargins(0, 0, 0, 0)
        
        scatter_point_view = QGraphicsView()
        scatter_point_view.setFixedWidth(15)
        training_point_layout.addWidget(scatter_point_view)

        scatter_point_scene = QGraphicsScene()
        scatter_point_view.setScene(scatter_point_scene)

        scatter_point = QGraphicsEllipseItem(0, 0, 10, 10)
        brush = QColor(color[0], color[1], color[2], color[3])
        scatter_point.setBrush(brush)

        scatter_point_scene.addItem(scatter_point)

        text_view = QGraphicsView()
        training_point_layout.addWidget(text_view)

        text_scene = QGraphicsScene()
        text_view.setScene(text_scene)

        text_item = QGraphicsTextItem('Training viewpoint')
        font = QFont('Inter')
        font.setPixelSize(14)
        text_item.setFont(font)
        text_scene.addItem(text_item)

    def draw_stddev_box(self, title, fraction, rect_size=20):
        uncertain_widget = QWidget()
        uncertain_widget.setFixedWidth(220)
        self.addWidget(uncertain_widget)

        uncertain_layout = QHBoxLayout(uncertain_widget)
        uncertain_layout.setContentsMargins(0, 0, 0, 0)

        uncertain_rect_view = QGraphicsView()
        uncertain_rect_view.setFixedWidth(rect_size*1.25)
        uncertain_layout.addWidget(uncertain_rect_view)

        uncertain_rect_scene = QGraphicsScene()
        uncertain_rect_view.setScene(uncertain_rect_scene)

        background_rect = QGraphicsRectItem(0, 0, rect_size, rect_size)

        stddev_size = rect_size*fraction
        edge_size = (rect_size-stddev_size)/2
        foreground_rect = QGraphicsRectItem(edge_size, edge_size, stddev_size, stddev_size)
        brush = QColor(0, 0, 0, 255)
        foreground_rect.setBrush(brush)

        uncertain_rect_scene.addItem(background_rect)
        uncertain_rect_scene.addItem(foreground_rect)

        text_view = QGraphicsView()
        uncertain_layout.addWidget(text_view)

        text_scene = QGraphicsScene()
        text_view.setScene(text_scene)

        text_item = QGraphicsTextItem(title)
        font = QFont('Inter')
        font.setPixelSize(14)
        text_item.setFont(font)
        text_scene.addItem(text_item)