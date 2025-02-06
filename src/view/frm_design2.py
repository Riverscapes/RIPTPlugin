
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets

from ..model.db_item import DBItem, DBItemModel, dict_factory
from ..model.project import Project
from ..model.event import Event, DESIGN_EVENT_TYPE_ID, DCE_EVENT_TYPE_ID, PLANNING_EVENT_TYPE_ID
from ..model.planning_container import PlanningContainer

from .frm_event import FrmEvent
from .widgets.planning_event_library import PlanningEventLibraryWidget

class FrmDesign(FrmEvent):

    def __init__(self, parent, qris_project: Project, event_type_id: int, event: Event = None):
        super().__init__(parent, qris_project, event_type_id, event)

        event_type = 'Design' if event_type_id == DESIGN_EVENT_TYPE_ID else 'As-Built Survey'
        self.setWindowTitle(f'Create New {event_type}' if event is None else f'Edit {event_type}')

        self.mandatory_layers = ['complexes']
        self.event_library = PlanningEventLibraryWidget(self, qris_project, [DCE_EVENT_TYPE_ID])

        self.lblPhase.setVisible(True)
        self.txtPhase.setVisible(True)

        self.lblPlatform.setVisible(False)
        self.cboPlatform.setVisible(False)
        
        # self.lblRepresentation.setVisible(False)
        # self.cboRepresentation.setVisible(False)
        self.lblDateLabel.setVisible(False)
        self.txtDateLabel.setVisible(False)

        self.lblPercentComplete = QtWidgets.QLabel('Percent Complete', self)
        self.lblPercentComplete.setToolTip('The percentage of the design that has been completed')
        self.tabGrid.addWidget(self.lblPercentComplete, 7, 0)

        self.horiz_slider = QtWidgets.QHBoxLayout()
        self.tabGrid.addLayout(self.horiz_slider, 7, 1, 1, 1)
        self.sliderPercentComplete = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.sliderPercentComplete.setMinimum(0)
        self.sliderPercentComplete.setMaximum(100)
        self.sliderPercentComplete.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.sliderPercentComplete.setTickInterval(5)
        self.sliderPercentComplete.setSingleStep(5)
        self.sliderPercentComplete.update()
        self.sliderPercentComplete.valueChanged.connect(self.adjustSliderValue)
        self.horiz_slider.addWidget(self.sliderPercentComplete)

        init_value = self.sliderPercentComplete.value()
        self.lblPercentCompleteValue = QtWidgets.QLabel(f'{init_value}%', self)
        font_metrics = QtGui.QFontMetrics(self.lblPercentCompleteValue.font())
        text_width = font_metrics.width("100%  ")
        text_height = font_metrics.height()
        self.lblPercentCompleteValue.setMinimumSize(text_width, text_height)
        self.lblPercentCompleteValue.setMaximumSize(text_width, text_height)
        self.horiz_slider.addWidget(self.lblPercentCompleteValue)

        self.lblStatus = QtWidgets.QLabel('Design Status Label', self)
        self.tabGrid.addWidget(self.lblStatus, 8, 0)

        statuses = {key: DBItem('', key, value) for key, value in enumerate(['In Progress', 'Provisional (awaiting review)', 'Final'])}
        self.cboStatus = QtWidgets.QComboBox(self)
        self.cboStatus.setToolTip('The status of the design')
        self.status_model = DBItemModel(statuses)
        self.cboStatus.setModel(self.status_model)
        self.tabGrid.addWidget(self.cboStatus, 8, 1, 1, 1)

        self.lblDesigners = QtWidgets.QLabel(self)
        self.lblDesigners.setText('Designers')
        self.tabGrid.addWidget(self.lblDesigners, 9, 0, 1, 1)

        self.txtDesigners = QtWidgets.QPlainTextEdit(self)
        self.txtDesigners.setToolTip('The name of the designer(s) of the design')
        self.tabGrid.addWidget(self.txtDesigners, 9, 1, 1, 1)

        # Create a checkbox widget for each design source
        self.design_source_widgets, self.design_sources = add_checkbox_widgets(
            self, self.qris_project.project_file, 'lkp_design_sources')

        # Add the checkboxes to the form
        self.lblDesignSources = QtWidgets.QLabel('Design Sources', self)
        self.lblDesignSources.setAlignment(QtCore.Qt.AlignTop)
        self.tabGrid.addWidget(self.lblDesignSources, 10, 0, 1, 1)
        self.groupBoxDesignSources = QtWidgets.QGroupBox(self)
        self.groupBoxDesignSources.setLayout(QtWidgets.QVBoxLayout())
        [self.groupBoxDesignSources.layout().addWidget(widget) for widget in self.design_source_widgets]
        self.tabGrid.addWidget(self.groupBoxDesignSources, 10, 1, 1, 1)

        surface_tab_index = self.tab.indexOf(self.surfaces_widget)
        self.tab.setTabText(surface_tab_index, 'Bases for Design')

        self.lblBasedOn = QtWidgets.QLabel('Data Capture Events', self)
        self.vert_surfaces.addWidget(self.lblBasedOn)

        self.grid_based_on_dces = QtWidgets.QGridLayout()
        self.vert_surfaces.addLayout(self.grid_based_on_dces)

        self.horiz_planning_container = QtWidgets.QHBoxLayout()
        self.vert_surfaces.addLayout(self.horiz_planning_container)

        self.lblPlanningContainer = QtWidgets.QLabel("Select DCE's From:", self)
        self.horiz_planning_container.addWidget(self.lblPlanningContainer)

        planning_containers = {key: value for key, value in self.qris_project.planning_containers.items()}
        planning_containers[0] = DBItem('None', 0, 'Manually Specify DCEs')
        planning_container_model = DBItemModel(planning_containers)
        planning_container_model._data.sort(key=lambda a: a[0])
        self.cboPlanningContainers = QtWidgets.QComboBox(self)
        self.cboPlanningContainers.setModel(planning_container_model)
        self.cboPlanningContainers.currentIndexChanged.connect(self.on_cboPlanningContainers_currentIndexChanged)
        self.horiz_planning_container.addWidget(self.cboPlanningContainers)

        self.vert_surfaces.addWidget(self.event_library)

        if event is not None:
            self.chkAddToMap.setVisible(False)

            if 'system' in self.metadata_widget.metadata:
                # if 'statusId' in self.metadata_widget.metadata['system']:
                #     status_id = self.metadata_widget.metadata['system']['statusId']
                #     status_index = self.status_model.getItemIndexById(status_id)
                #     self.cboStatus.setCurrentIndex(status_index)

                if 'status' in self.metadata_widget.metadata['system']:
                    status = self.metadata_widget.metadata['system']['status']
                    status_index = self.status_model.getItemIndexByName(status)
                    self.cboStatus.setCurrentIndex(status_index)

                if 'designers' in self.metadata_widget.metadata['system']:
                    self.txtDesigners.setPlainText(self.metadata_widget.metadata['system']['designers'])

                if 'designSourceIds' in self.metadata_widget.metadata['system']:
                    design_source_ids = self.metadata_widget.metadata['system']['designSourceIds']
                    if design_source_ids is not None:
                        for source_id in design_source_ids:
                            for widget in self.design_source_widgets:
                                widget_id = widget.property('id')
                                if widget_id == source_id:
                                    widget.setChecked(True)
                if 'percentComplete' in self.metadata_widget.metadata['system']:
                    self.sliderPercentComplete.setValue(int(self.metadata_widget.metadata['system']['percentComplete']))

                if 'planningContainerId' in self.metadata_widget.metadata['system']:
                    planning_container_id = self.metadata_widget.metadata['system']['planningContainerId']
                    planning_container: PlanningContainer = self.qris_project.planning_containers[planning_container_id]
                    planning_container_index = self.cboPlanningContainers.findData(planning_container)
                    self.cboPlanningContainers.setCurrentIndex(planning_container_index)
                elif 'planning_events' in self.metadata_widget.metadata['system']:
                    planning_events = {int(k): int(v) for k,v in self.metadata_widget.metadata['system']['planning_events'].items()}
                    self.event_library.load_events([self.qris_project.events[int(event_id)] for event_id in planning_events.keys()])
                    self.event_library.set_event_ids(planning_events)
                    self.event_library.setEnabled(True)
                else:
                    self.event_library.setEnabled(True)

                # if 'based_on_exising_dce_id' in self.metadata_widget.metadata['system']:
                #     existing_dce_id = self.metadata_widget.metadata['system']['based_on_exising_dce_id']
                #     existing_dce_index = self.existing_dce_model.getItemIndexById(existing_dce_id)
                #     self.cboExistingDCEs.setCurrentIndex(existing_dce_index)
                
                # if 'based_on_historical_dce_id' in self.metadata_widget.metadata['system']:
                #     historical_dce_id = self.metadata_widget.metadata['system']['based_on_historical_dce_id']
                #     historical_dce_index = self.historical_dce_model.getItemIndexById(historical_dce_id)
                #     self.cboHistoricalDCEs.setCurrentIndex(historical_dce_index)

                # if 'based_on_planning_dce_id' in self.metadata_widget.metadata['system']:
                #     planning_dce_id = self.metadata_widget.metadata['system']['based_on_planning_dce_id']
                #     planning_dce_index = self.future_recovery_dce_model.getItemIndexById(planning_dce_id)
                #     self.cboFutureRecoveryDCEs.setCurrentIndex(planning_dce_index) 

        else:
            # iterate through the tree model and children to find the first 'structure_points' layer
            for index in range(self.layer_widget.tree_model.rowCount()):
                protocol_item = self.layer_widget.tree_model.item(index)
                for layer_index in range(protocol_item.rowCount()):
                    layer_item = protocol_item.child(layer_index)
                    if 'complexes' in layer_item.data(QtCore.Qt.UserRole).id:
                        self.layer_widget.add_selected_layers(layer_item)

    def on_cboPlanningContainers_currentIndexChanged(self, index):

        # if the user selects 'Manually Specify DCEs' then enable the event library. 
        # Otherwise, disable the event library and set the events based on the selected planning container
        if index == 0:
            self.event_library.setEnabled(True)
        else:
            planning_container_id = self.cboPlanningContainers.currentData(QtCore.Qt.UserRole).id
            planning_container: PlanningContainer = self.qris_project.planning_containers[planning_container_id]
            self.event_library.load_events([self.qris_project.events[event_id] for event_id in planning_container.planning_events.keys()])
            self.event_library.set_event_ids(planning_container.planning_events)
            self.event_library.setEnabled(False)

    def adjustSliderValue(self, value):
        # Calculate the nearest multiple of 5
        adjusted_value = round(value / 5) * 5
        # Set the slider's value to this adjusted value
        # Block signals to prevent infinite loop
        self.sliderPercentComplete.blockSignals(True)
        self.sliderPercentComplete.setValue(adjusted_value)
        self.sliderPercentComplete.blockSignals(False)
        # Update the label
        self.lblPercentCompleteValue.setText(f'{adjusted_value}%')

    def accept(self):

        self.metadata_widget.add_system_metadata('statusId', self.cboStatus.currentData(QtCore.Qt.UserRole).id)
        self.metadata_widget.add_system_metadata('designers', self.txtDesigners.toPlainText())

        design_source_ids = []
        for widget in self.design_source_widgets:
            if widget.isChecked() is True:
                design_source_ids.append(widget.property('id'))

        if len(design_source_ids) > 0:
            self.metadata_widget.add_system_metadata('designSourceIds', design_source_ids)
        else:
            if 'designSourceIds' in self.metadata_widget.metadata['system']:
                self.metadata_widget.delete_item('system', 'designSourceIds')

        self.metadata_widget.add_system_metadata('status', self.cboStatus.currentData(QtCore.Qt.UserRole).name)
        self.metadata_widget.add_system_metadata('percentComplete', self.sliderPercentComplete.value())

        if self.cboPlanningContainers.currentIndex() == 0:
            if 'planningContainerId' in self.metadata_widget.metadata['system']:
                self.metadata_widget.delete_item('system', 'planningContainerId')
            # see if any events have been selected manually. if so, then add them to the metadata as a list of event_id and representation_id named 'planning_events'
            planning_events = self.event_library.get_event_values()
            if len(planning_events) > 0:
                self.metadata_widget.add_system_metadata('planning_events', planning_events)
        else:
            planning_container_id = self.cboPlanningContainers.currentData(QtCore.Qt.UserRole).id
            self.metadata_widget.add_system_metadata('planningContainerId', planning_container_id)
            if 'planning_events' in self.metadata_widget.metadata['system']:
                self.metadata_widget.delete_item('system', 'planning_events')

        # existing_dce_id = self.cboExistingDCEs.currentData(QtCore.Qt.UserRole).id
        # self.metadata_widget.add_system_metadata('based_on_exising_dce_id', existing_dce_id)

        # historical_dce_id = self.cboHistoricalDCEs.currentData(QtCore.Qt.UserRole).id
        # self.metadata_widget.add_system_metadata('based_on_historical_dce_id', historical_dce_id)

        # future_recovery_dce_id = self.cboFutureRecoveryDCEs.currentData(QtCore.Qt.UserRole).id
        # self.metadata_widget.add_system_metadata('based_on_planning_dce_id', future_recovery_dce_id)

        super().accept()


def add_checkbox_widgets(parent_widget, db_path, table_name):

    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute(f'SELECT * FROM {table_name}')
    data = {row['id']: row['name'] for row in curs.fetchall()}
    widget_list = []
    for id, name in data.items():
        widget = QtWidgets.QCheckBox(parent_widget)
        widget.setText(name)
        widget.setProperty('id', id)
        widget_list.append(widget)

    return widget_list, data
