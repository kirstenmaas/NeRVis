from PyQt6.QtWidgets import QHBoxLayout, QLabel, QButtonGroup, QRadioButton, QWidget

import pdb

class ProjectionButtonLayout(QHBoxLayout):
    def __init__(self, parent, update_state=None):
        super().__init__(parent)

        self.widget = QWidget()
        self.update_state = update_state

        self.setContentsMargins(0, 0, 0, 0)

        self.EQUAL_AREA = 'Equal-area'
        self.EQUIDISTANT = 'Equidistant'

        self.radio_button_state = self.EQUIDISTANT

        self.create_toggle_buttons()
        self.create_layout()
    
    def create_toggle_buttons(self):
        group = QButtonGroup()

        self.area_button = QRadioButton(self.EQUAL_AREA)
        self.equi_button = QRadioButton(self.EQUIDISTANT)
        group.addButton(self.equi_button)
        group.addButton(self.area_button)

        self.radio_button_objects = {
            self.EQUAL_AREA: self.area_button,
            self.EQUIDISTANT: self.equi_button,
        }
        
        self.radio_button_objects[self.EQUIDISTANT].setChecked(True)
        self.radio_button_objects[self.EQUAL_AREA].setChecked(False)

        self.group = group
    
    def create_layout(self):
        layout = QHBoxLayout()

        label = QLabel("Projection type:")
        layout.addWidget(label)
        layout.addWidget(self.equi_button)
        layout.addWidget(self.area_button)

        self.widget.setLayout(layout)
        self.widget.group = self.group
        self.group.buttonClicked.connect(self.check_radio_button)
        self.addWidget(self.widget)

    def set_button_state(self, button_name, state):
        if button_name in [self.EQUAL_AREA, self.EQUIDISTANT]:
            self.radio_button_objects[button_name].setChecked(state)

        if state:
            self.radio_button_state = button_name
    
    def check_radio_button(self, radio_button):
        buttonName = radio_button.text()

        # button is on so turn it off and turn the other one on
        if self.radio_button_state == buttonName:
            if buttonName == self.EQUAL_AREA:
                self.set_button_state(self.EQUAL_AREA, False)
                self.set_button_state(self.EQUIDISTANT, True)
            else:
                self.set_button_state(self.EQUAL_AREA, True)
                self.set_button_state(self.EQUIDISTANT, False)
        # button is off so turn it on and turn the other one off
        else:
            if buttonName == self.EQUAL_AREA:
                self.set_button_state(self.EQUAL_AREA, True)
                self.set_button_state(self.EQUIDISTANT, False)
            else:
                self.set_button_state(self.EQUAL_AREA, False)
                self.set_button_state(self.EQUIDISTANT, True)
        self.update_state()

class ExtremeButtonLayout(QHBoxLayout):
    def __init__(self, parent, update_state=None):
        super().__init__(parent)

        self.widget = QWidget()
        self.update_state = update_state

        self.setContentsMargins(0, 0, 0, 0)

        self.STANDARD_DEVIATION = 'Standard deviation'
        self.MAXIMUM = 'Maximum'

        self.radio_button_state = self.STANDARD_DEVIATION

        self.create_toggle_buttons()
        self.create_layout()
    
    def create_toggle_buttons(self):
        group = QButtonGroup()

        self.stddev_button = QRadioButton(self.STANDARD_DEVIATION)
        self.max_button = QRadioButton(self.MAXIMUM)
        group.addButton(self.stddev_button)
        group.addButton(self.max_button)

        self.radio_button_objects = {
            self.STANDARD_DEVIATION: self.stddev_button,
            self.MAXIMUM: self.max_button,
        }
        
        self.radio_button_objects[self.STANDARD_DEVIATION].setChecked(True)
        self.radio_button_objects[self.MAXIMUM].setChecked(False)

        self.group = group

    def create_layout(self):
        layout = QHBoxLayout()

        label = QLabel("Aggregation type:")
        layout.addWidget(label)
        layout.addWidget(self.stddev_button)
        layout.addWidget(self.max_button)

        self.widget.setLayout(layout)
        self.widget.group = self.group
        self.group.buttonClicked.connect(self.check_radio_button)
        self.addWidget(self.widget)

    def set_button_state(self, button_name, state):
        if button_name in [self.STANDARD_DEVIATION, self.MAXIMUM]:
            self.radio_button_objects[button_name].setChecked(state)
        if state:
            self.radio_button_state = button_name

    def check_radio_button(self, radio_button):
        buttonName = radio_button.text()

        # button is on so turn it off and turn the other one on
        if self.radio_button_state == buttonName:
            if buttonName == self.STANDARD_DEVIATION:
                self.set_button_state(self.STANDARD_DEVIATION, False)
                self.set_button_state(self.MAXIMUM, True)
            else:
                self.set_button_state(self.STANDARD_DEVIATION, True)
                self.set_button_state(self.MAXIMUM, False)
        # button is off so turn it on and turn the other one off
        else:
            if buttonName == self.STANDARD_DEVIATION:
                self.set_button_state(self.STANDARD_DEVIATION, True)
                self.set_button_state(self.MAXIMUM, False)
            else:
                self.set_button_state(self.STANDARD_DEVIATION, False)
                self.set_button_state(self.MAXIMUM, True)
        self.update_state()

class RadioButtonLayout(QHBoxLayout):
    def __init__(self, parent, all_heatmaps):
        super().__init__(parent)

        self.setContentsMargins(0, 0, 0, 0)
        self.all_heatmaps = all_heatmaps

        self.projection_button_widget = QWidget()
        self.projection_button_layout = ProjectionButtonLayout(self.projection_button_widget, update_state=self.update_state)
        self.projection_button_widget.setLayout(self.projection_button_layout)
        self.addWidget(self.projection_button_widget)

        self.extreme_button_widget = QWidget()
        self.extreme_button_layout = ExtremeButtonLayout(self.extreme_button_widget, update_state=self.update_state)
        self.extreme_button_widget.setLayout(self.extreme_button_layout)
        self.addWidget(self.extreme_button_widget)

    def update_state(self):
        for heatmap_layout in self.all_heatmaps:
            heatmap_layout.reset_heatmap(self.projection_button_layout.radio_button_state, self.extreme_button_layout.radio_button_state)

        