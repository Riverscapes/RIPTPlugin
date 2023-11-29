from PyQt5 import QtCore, QtWidgets
from qgis.core import Qgis, QgsApplication
from qgis.utils import iface

from ..model.project import Project
from ..model.db_item import DBItem
from ..gp.feature_class_functions import get_field_names, get_field_values
from ..gp.import_feature_class import ImportFeatureClass, ImportFieldMap

from .frm_field_value_map import FrmFieldValueMap
from .utilities import add_standard_form_buttons

from typing import List


class FrmImportDceLayer(QtWidgets.QDialog):

    import_complete = QtCore.pyqtSignal(bool)

    def __init__(self, parent, project: Project, db_item: DBItem, import_path: str):

        self.qris_project = project
        self.db_item = db_item
        self.import_path = import_path
        source = 'dce_points' if db_item.layer.geom_type == 'Point' else 'dce_lines' if db_item.layer.geom_type == 'Linestring' else 'dce_polygons'
        self.target_path = f'{project.project_file}|layername={source}'
        self.qris_event = next((event for event in self.qris_project.events.values() if event.id == db_item.event_id), None)
        self.field_status = None
        self.field_maps: List[ImportFieldMap] = []
        self.input_fields, self.input_field_types = get_field_names(self.import_path)
        # self.target_fields, self.target_field_types = get_field_names(self.target_path)
        # Get the fields from the layer metadata if it exists
        self.target_fields = {}
        if self.db_item.layer.metadata is not None:
            if 'fields' in self.db_item.layer.metadata.keys():
                for field in self.db_item.layer.metadata['fields']:
                    self.target_fields[field['label']] = field

        super(FrmImportDceLayer, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle('Import DCE Layer From Existing Feature Class')
        self.txtInputFC.setText(self.import_path)
        self.txtTargetFC.setText(self.db_item.layer.fc_name)
        self.txtEvent.setText(self.qris_event.name)

        self.load_fields()

    def load_fields(self):

        self.tblFields.clearContents()

        # create a row for each target field and load the field name
        self.tblFields.setRowCount(len(self.input_fields))
        for i, field in enumerate(self.input_fields):
            self.tblFields.setItem(i, 0, QtWidgets.QTableWidgetItem(field))
            self.tblFields.setItem(i, 1, QtWidgets.QTableWidgetItem(self.input_field_types[i]))
            # create a combo box and load the input fields
            combo = QtWidgets.QComboBox()
            # filtered_input_fields = [field for field, field_type in zip(input_fields, input_field_types) if field_type == target_field_types[i]]
            combo.addItems(['-- Do Not Import --', 'Add to Metadata'])
            items = {}
            for target_field_name, target_field in self.target_fields.items():
                if target_field_name in ['event_id', 'metadata']:
                    continue
                if target_field['type'] == self.input_field_types[i]:
                    item = f'Direct Copy to {target_field_name}'
                    # else:
                    #     item = f'Map values to {target_field}'
                    items[field] = item
                    combo.addItem(item)
            # add map values option for string or integer types
            if self.input_field_types[i] in ['String', 'Integer']:
                values = list(set(get_field_values(self.import_path, field)))
                if not(len(values) == 1 and values[0] is None):
                    combo.addItem('Map Values')
            self.tblFields.setCellWidget(i, 2, combo)
            if self.field_status is not None:
                combo.setCurrentIndex(self.field_status[i])
            else:
                # if the target field name matches the input field name then select it
                if field in items.keys():
                    combo.setCurrentIndex(combo.findText(items[field]))
                else:
                    combo.setCurrentIndex(0)
            # add button to open value map dialog
            btn = QtWidgets.QPushButton('Map Values...')
            btn.clicked.connect(self.on_btn_clicked)
            self.tblFields.setCellWidget(i, 3, btn)

            combo.currentIndexChanged.connect(self.combo_changed)

        self.tblFields.resizeColumnsToContents()
        self.combo_changed()

    def on_btn_clicked(self):

        # get the row and column of the button that was clicked
        btn = self.sender()
        row = self.tblFields.indexAt(btn.pos()).row()

        # get the field name
        input_field = self.tblFields.item(row, 0).text()

        # get the field values
        values = get_field_values(self.import_path, input_field)
        # get dict of target fields and values
        fields = {}
        for target_field_name, target_field in self.target_fields.items():
            if target_field_name in ['event_id', 'metadata']:
                continue
            # find the lookup table in the project that matches the field name
            if 'lookup' in target_field.keys():
                fields[target_field_name] = self.qris_project.lookup_values[target_field['lookup']]

        # open the value map dialog
        frm = FrmFieldValueMap(self, input_field, values, fields)
        if input_field in [field.src_field for field in self.field_maps]:
            in_field = next((field for field in self.field_maps if field.src_field == input_field), None)
            frm.load_field_value_map(in_field)
        frm.field_value_map.connect(self.on_field_value_map)
        frm.exec_()

    def on_field_value_map(self, field_name: str, field_value_map: dict, retain: bool):

        # add or replace the field value map for the field
        if field_name in [field.src_field for field in self.field_maps]:
            self.field_maps.remove(next((field for field in self.field_maps if field.src_field == field), None))
        if retain is True:
            field_map = ImportFieldMap(field_name, field_name, map=field_value_map)
        else:
            field_map = ImportFieldMap(field_name, map=field_value_map)
        self.field_maps.append(field_map)

    def combo_changed(self):

        # disable button if Map Values is not is selected for each row
        for i in range(self.tblFields.rowCount()):
            combo: QtWidgets.QComboBox = self.tblFields.cellWidget(i, 2)
            btn: QtWidgets.QPushButton = self.tblFields.cellWidget(i, 3)
            if combo.currentText() == 'Map Values':
                btn.setEnabled(True)
            else:
                btn.setEnabled(False)

    def validate_fields(self):

        # check that none of the input fields are duplicated, except for the 'Do Not Import' option
        input_fields = []
        valid = True
        for i in range(self.tblFields.rowCount()):
            combo: QtWidgets.QComboBox = self.tblFields.cellWidget(i, 2)
            if combo.currentText() not in ['-- Do Not Import --', 'Add to Metadata', "Map Values"]:
                input_fields.append(combo.currentText())

        for i in range(self.tblFields.rowCount()):
            combo = self.tblFields.cellWidget(i, 2)
            if len(input_fields) == len(set(input_fields)):
                # set the combo box back to original text color
                combo.setStyleSheet('')
                combo.setToolTip('')
            else:
                if combo.currentIndex() > 0 and input_fields.count(combo.currentText()) > 1:
                    combo.setStyleSheet('color: red')
                    # add a tool tip to explain the error
                    combo.setToolTip('Duplicate input field imports not allowed')
                    valid = False
                else:
                    combo.setStyleSheet('')
                    combo.setToolTip('')

        return valid

    def accept(self):

        if not self.validate_fields():
            return

        # get list of fields where the combo box is set to add to metadata
        for i in range(self.tblFields.rowCount()):
            combo: QtWidgets.QComboBox = self.tblFields.cellWidget(i, 2)
            if combo.currentText() == 'Add to Metadata':
                field_name = self.tblFields.item(i, 0).text()
                field_map = ImportFieldMap(field_name, field_name)
                self.field_maps.append(field_map)
            # if "Direct Copy to " in combo.currentText():
            #     self.field_maps.update({self.tblFields.item(i, 0).text(): combo.currentText().replace("Direct Copy to ", "")})

        try:
            layer_attributes = {'event_id': self.db_item.event_id, 'event_layer_id': self.db_item.layer.id}
            import_task = ImportFeatureClass(self.import_path, self.target_path, layer_attributes, self.field_maps)
            self.buttonBox.setEnabled(False)
            # DEBUG
            # result = import_task.run()
            # source_feats = import_task.in_feats
            # out_feats = import_task.out_feats
            # skip_feats = import_task.skipped_feats
            # self.on_import_complete(result, source_feats, out_feats, skip_feats)
            # PRODUCTION
            import_task.import_complete.connect(self.on_import_complete)
            QgsApplication.taskManager().addTask(import_task)
        except Exception as ex:
            self.exception = ex
            self.buttonBox.setEnabled(True)
            return False

    def on_import_complete(self, result: bool, source_feats: int, out_feats: int, skip_feats: int):

        if result is True:
            extra_message = '' if source_feats == out_feats else f' (additional features were created due to exploding multi-part geometries.)'
            extra_message += f' {skip_feats} features were skipped due to missing geometry.'
            iface.messageBar().pushMessage('Import Feature Class Complete.', f"Successfully imported {source_feats} features from {self.import_path} to {out_feats} features in {self.db_item.layer.fc_name}.{extra_message}", level=Qgis.Info, duration=5)
            iface.mapCanvas().refreshAllLayers()
            iface.mapCanvas().refresh()
            self.import_complete.emit(result)
            super(FrmImportDceLayer, self).accept()
        else:
            iface.messageBar().pushMessage('Feature Class Copy Error', 'Review the QGIS log.', level=Qgis.Critical, duration=5)
            self.buttonBox.setEnabled(True)

    def on_rdoImport_clicked(self):

        # if radio button is checked then enable the table
        if self.rdoImport.isChecked():
            self.tblFields.setEnabled(True)
            self.load_fields()
        else:
            self.field_status = []
            # set all combo boxes to 'Do Not Import'
            for i in range(self.tblFields.rowCount()):
                combo: QtWidgets.QComboBox = self.tblFields.cellWidget(i, 2)
                self.field_status.append(combo.currentIndex())
                combo.setCurrentIndex(0)
            self.tblFields.setEnabled(False)

    def setupUi(self):

        self.resize(500, 500)
        self.setMinimumSize(300, 200)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblInputFC = QtWidgets.QLabel('Input Feature Class')
        self.grid.addWidget(self.lblInputFC, 0, 0)
        self.txtInputFC = QtWidgets.QLineEdit()
        self.txtInputFC.setReadOnly(True)
        self.grid.addWidget(self.txtInputFC, 0, 1)

        self.lblEvent = QtWidgets.QLabel('Data Capture Event')
        self.grid.addWidget(self.lblEvent, 1, 0)
        self.txtEvent = QtWidgets.QLineEdit()
        self.txtEvent.setReadOnly(True)
        self.grid.addWidget(self.txtEvent, 1, 1)

        self.lblTargetFC = QtWidgets.QLabel('Target Layer')
        self.grid.addWidget(self.lblTargetFC, 2, 0)
        self.txtTargetFC = QtWidgets.QLineEdit()
        self.txtTargetFC.setReadOnly(True)
        self.grid.addWidget(self.txtTargetFC, 2, 1)

        self.lblFields = QtWidgets.QLabel('Fields')
        self.grid.addWidget(self.lblFields, 3, 0)

        self.horiz = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz, 3, 1)

        self.rdoImport = QtWidgets.QRadioButton('Import Fields')
        self.rdoImport.setChecked(True)
        self.rdoImport.clicked.connect(self.on_rdoImport_clicked)
        self.horiz.addWidget(self.rdoImport)

        self.rdoIgnore = QtWidgets.QRadioButton('Ignore Fields')
        self.rdoIgnore.clicked.connect(self.on_rdoImport_clicked)
        self.horiz.addWidget(self.rdoIgnore)

        self.horiz.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

        self.tblFields = QtWidgets.QTableWidget()
        self.tblFields.setColumnCount(4)
        self.tblFields.setHorizontalHeaderLabels(['Input Fields', 'Data Type', 'Actions', ""])
        # self.tblFields.horizontalHeader().setStretchLastSection(True)
        # self.tblFields.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tblFields.verticalHeader().setVisible(False)
        self.tblFields.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tblFields.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.vert.addWidget(self.tblFields)

        self.vert.addLayout(add_standard_form_buttons(self, 'import_dce_layer'))
