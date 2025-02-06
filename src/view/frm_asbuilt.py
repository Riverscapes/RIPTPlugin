
import json
import sqlite3

from PyQt5 import QtCore, QtGui, QtWidgets

from ..model.db_item import DBItem, DBItemModel, dict_factory
from ..model.event_layer import EventLayer
from ..model.project import Project
from ..model.event import Event, DESIGN_EVENT_TYPE_ID, AS_BUILT_EVENT_TYPE_ID, DCE_EVENT_TYPE_ID
from ..model.datespec import DateSpec

from .frm_event import FrmEvent
from .frm_date_picker import FrmDatePicker

class FrmAsBuilt(FrmEvent):

    def __init__(self, parent, qris_project: Project, event_type_id: int, event: Event = None):
        super().__init__(parent, qris_project, event_type_id, event)

        event_type = 'As-Built'
        self.setWindowTitle(f'Create New {event_type}' if event is None else f'Edit {event_type}')

        self.lblPhase.setVisible(True)
        self.txtPhase.setVisible(True)

        self.lblAssociatedDesign = QtWidgets.QLabel('Design this As-Built is based on', self)
        self.tabGrid.addWidget(self.lblAssociatedDesign, 1, 0)

        self.cboAssociatedDesign = QtWidgets.QComboBox(self)
        self.cboAssociatedDesign.setToolTip('Select the design that this as-built is based on.')
        self.tabGrid.addWidget(self.cboAssociatedDesign, 1, 1, 1, 1)
        designs:dict = {design_id: design for design_id, design in qris_project.events.items() if design.event_type.id == DESIGN_EVENT_TYPE_ID}
        designs[0] = DBItem('', 0, 'None')
        self.associated_design_model = DBItemModel(designs)
        self.associated_design_model.sort_data_by_key()
        self.cboAssociatedDesign.setModel(self.associated_design_model)

        self.optSingleDate.setVisible(False)
        self.optDateRange.setVisible(False)

        self.lblStartDate.setText('Date of As-Built Survey')

        self.lblConstructionDate = QtWidgets.QLabel('Date of Construction', self)
        self.tabGrid.addWidget(self.lblConstructionDate, 6, 0)

        self.uc_construction = FrmDatePicker(self)
        self.tabGrid.addWidget(self.uc_construction, 6, 1)

        self.lblPlatform.setVisible(False)
        self.cboPlatform.setVisible(False)

        # self.lblRepresentation.setVisible(False)
        # self.cboRepresentation.setVisible(False)
        self.lblDateLabel.setVisible(False)
        self.txtDateLabel.setVisible(False)

        self.lblDesigners = QtWidgets.QLabel('Observer(s)', self)
        self.tabGrid.addWidget(self.lblDesigners, 8, 0, 1, 1)
        self.tabGrid.setAlignment(self.lblDesigners, QtCore.Qt.AlignTop)

        self.txtDesigners = QtWidgets.QPlainTextEdit(self)
        self.txtDesigners.setToolTip('Enter the name(s) of the person(s) who observed the as-built survey.')
        self.tabGrid.addWidget(self.txtDesigners, 8, 1, 1, 1)

        # Create a checkbox widget for each design source
        self.design_source_widgets, self.design_sources = add_checkbox_widgets(
            self, self.qris_project.project_file, 'lkp_design_sources')

        # Add the checkboxes to the form
        self.lblDesignSources = QtWidgets.QLabel('As-Built Observations', self)
        self.lblDesignSources.setAlignment(QtCore.Qt.AlignTop)
        self.tabGrid.addWidget(self.lblDesignSources, 9, 0, 1, 1)
        self.groupBoxDesignSources = QtWidgets.QGroupBox(self)
        self.groupBoxDesignSources.setLayout(QtWidgets.QVBoxLayout())
        [self.groupBoxDesignSources.layout().addWidget(widget) for widget in self.design_source_widgets]
        # add vertical spacer to group box layout

        self.tabGrid.addWidget(self.groupBoxDesignSources, 9, 1)
        self.tabGrid.setAlignment(self.groupBoxDesignSources, QtCore.Qt.AlignTop)

        surface_tab_index = self.tab.indexOf(self.surfaces_widget)
        self.tab.setTabText(surface_tab_index, 'Bases for As-Built')

        self.horiz_corresponding_dce = QtWidgets.QHBoxLayout()
        self.vert_surfaces.addLayout(self.horiz_corresponding_dce)

        self.lblAssociatedDCE = QtWidgets.QLabel('Corresponding Data Capture Event', self)
        self.horiz_corresponding_dce.addWidget(self.lblAssociatedDCE)

        self.cboAssociatedDCE = QtWidgets.QComboBox(self)
        self.horiz_corresponding_dce.addWidget(self.cboAssociatedDCE)

        dces = {dce_id: dce for dce_id, dce in qris_project.events.items() if dce.event_type.id == DCE_EVENT_TYPE_ID}
        dces[0] = DBItem('', 0, 'None')
        self.associated_dce_model = DBItemModel(dces)
        self.associated_dce_model.sort_data_by_key()
        self.cboAssociatedDCE.setModel(self.associated_dce_model)

        # self.btn_pick_dce_by_date = QtWidgets.QPushButton('By Nearest Date', self)
        # self.btn_pick_dce_by_date.clicked.connect(self.pick_dce_by_date)
        # self.horiz_corresponding_dce.addWidget(self.btn_pick_dce_by_date)

        if event is not None:
            self.chkAddToMap.setVisible(False)
            if 'system' in self.metadata_widget.metadata:
                if 'designers' in self.metadata_widget.metadata['system']:
                    # Keep compatibility with older versions of the metadata
                    self.txtDesigners.setPlainText(self.metadata_widget.metadata['system']['designers'])
                elif 'observers' in self.metadata_widget.metadata['system']:
                    self.txtDesigners.setPlainText(self.metadata_widget.metadata['system']['observers'])

                if 'designSourceIds' in self.metadata_widget.metadata['system']:
                    design_source_ids = self.metadata_widget.metadata['system']['designSourceIds']
                    if design_source_ids is not None:
                        for source_id in design_source_ids:
                            for widget in self.design_source_widgets:
                                widget_id = widget.property('id')
                                if widget_id == source_id:
                                    widget.setChecked(True)

                if 'associatedDesignId' in self.metadata_widget.metadata['system']:
                    associated_design_id = self.metadata_widget.metadata['system']['associatedDesignId']
                    associated_design_index = self.associated_design_model.getItemIndexById(associated_design_id)
                    self.cboAssociatedDesign.setCurrentIndex(associated_design_index)

                if 'constructionDate' in self.metadata_widget.metadata['system']:
                    # parse the date string
                    construction_date_json = self.metadata_widget.metadata['system']['constructionDate']
                    try:
                        construction_date_dict = json.loads(construction_date_json)
                    except json.JSONDecodeError:
                        construction_date_dict = None
                        # manually extract the date parts from the string
                        construction_date_parts = construction_date_json.strip('{}').split(', ')
                        construction_date_dict = {}
                        for part in construction_date_parts:
                            key, value = part.split(': ')
                            construction_date_dict[key.strip('"\'')] = int(value.strip('"\'')) if value.strip('"\'') != 'None' else None
                    # create a DateSpec object from the dictionary
                    construction_date = DateSpec(
                        construction_date_dict.get('year', None),
                        construction_date_dict.get('month', None),
                        construction_date_dict.get('day', None)
                    )
                    # set the date in the date picker
                    self.uc_construction.set_date_spec(construction_date)
                
                if 'associatedDCE_Id' in self.metadata_widget.metadata['system']:
                    associatedDCE_Id = self.metadata_widget.metadata['system']['associatedDCE_Id']
                    associatedDCE_index = self.associated_dce_model.getItemIndexById(associatedDCE_Id)
                    self.cboAssociatedDCE.setCurrentIndex(associatedDCE_index)
        
        else:
            # iterate through the tree model and children to find the first 'structure_points' layer
            for index in range(self.layer_widget.tree_model.rowCount()):
                protocol_item = self.layer_widget.tree_model.item(index)
                for layer_index in range(protocol_item.rowCount()):
                    layer_item = protocol_item.child(layer_index)
                    if 'structure_points' in layer_item.data(QtCore.Qt.UserRole).id:
                        self.layer_widget.add_selected_layers(layer_item)
                

    def pick_dce_by_date(self):
        # TODO: This is tricky, because parts of the dates may be None

        # Get the date of this event in the form
        event_date = self.uc_start.get_date_spec()

        # Get the date of the DCEs, some may be none
        dce_dates = {}
        dce: Event
        for i in range(self.associated_dce_model.rowCount(0)):
            dce = self.associated_dce_model.data(self.associated_dce_model.index(i), QtCore.Qt.UserRole)
            if dce.date is not None:
                year, month, day = dce.date.split('-')
                year = int(year) if year != 'None' else None
                month = int(month) if month != 'None' else None
                day = int(day) if day != 'None' else None
                dce_dates[dce.id] = DateSpec(year, month, day)
            else:
                dce_dates[dce.id] = None
            
        # Find the DCE with the nearest date to the event date
        nearest_dce_id = None
        nearest_dce_diff = None
        for dce_id, dce_date in dce_dates.items():
            if dce_date is not None:
                diff = dce_date - event_date
                if nearest_dce_diff is None or diff < nearest_dce_diff:
                    nearest_dce_id = dce_id
                    nearest_dce_diff = diff

        if nearest_dce_id is not None:
            dce_index = self.associated_dce_model.getItemIndexById(nearest_dce_id)
            self.cboAssociatedDCE.setCurrentIndex(dce_index)
        else:
            self.cboAssociatedDCE.setCurrentIndex(0)


    def accept(self):

        # there must be at least one 'structure_points' or 'structure_lines' layer selected
        selected_layers = []
        for index in range(self.layer_widget.layers_model.rowCount()):
            item = self.layer_widget.layers_model.item(index)
            selected_layers.append(item.data(QtCore.Qt.UserRole).fc_name)
        if any('structure_points' in layer or 'structure_lines' in layer for layer in selected_layers) is False:
            QtWidgets.QMessageBox.critical(self, 'Error', 'At least one structure layer must be selected.')
            return

        self.metadata_widget.add_system_metadata('observers', self.txtDesigners.toPlainText())

        if self.cboAssociatedDesign.currentData(QtCore.Qt.UserRole).id != 0:
            self.metadata_widget.add_system_metadata('associatedDesignId', self.cboAssociatedDesign.currentData(QtCore.Qt.UserRole).id)
        else:
            self.metadata_widget.delete_item('system', 'associatedDesignId')

        construction_date = self.uc_construction.get_date_spec()
        # parse the construction date into a dictionary
        dict_construction_date = {
            'year': construction_date.year,
            'month': construction_date.month,
            'day': construction_date.day
        }
        # check if all parts of the date are None
        if all(value is None for value in dict_construction_date.values()):
            # if all parts of the date are None, remove the construction date from the metadata
            self.metadata_widget.delete_item('system', 'constructionDate')
        else:
            # Remove the None values from the dictionary, then convert to a json string
            construction_date_str = json.dumps({key: value for key, value in dict_construction_date.items() if value is not None})
            self.metadata_widget.add_system_metadata('constructionDate', construction_date_str)

        design_source_ids = []
        for widget in self.design_source_widgets:
            if widget.isChecked() is True:
                design_source_ids.append(widget.property('id'))

        if len(design_source_ids) > 0:
            self.metadata_widget.add_system_metadata('designSourceIds', design_source_ids)
        else:
            self.metadata_widget.delete_item('system', 'designSourceIds')

        if self.cboAssociatedDCE.currentData(QtCore.Qt.UserRole).id != 0:
            self.metadata_widget.add_system_metadata('associatedDCE_Id', self.cboAssociatedDCE.currentData(QtCore.Qt.UserRole).id)
        else:
            self.metadata_widget.delete_item('system', 'associatedDCE_Id')

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
