import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from qgis.core import Qgis, QgsApplication, QgsMessageLog, QgsTask

from ..model.raster import Raster, insert_raster, SURFACES_PARENT_FOLDER, CONTEXT_PARENT_FOLDER
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project
from ..model.mask import AOI_MASK_TYPE_ID

from ..gp.copy_raster import CopyRaster
from ..gp.create_hillshade import Hillshade
from .utilities import validate_name_unique, validate_name, add_standard_form_buttons


class FrmRaster(QtWidgets.QDialog):

    def __init__(self, parent, iface, project: Project, import_source_path: str, is_context: bool, raster: Raster = None):

        self.iface = iface
        self.project = project
        self.is_context = is_context
        self.raster = raster
        self.hillshade_raster_path = None
        self.hillshade = None

        super(FrmRaster, self).__init__(parent)
        self.setupUi()

        raster_types = {id: db_item for id, db_item in project.lookup_tables['lkp_raster_types'].items()}

        # If scratch raster then exclude BaseMaps
        # if self.is_context is True:
        raster_types.pop(2)  # Remove type basemap

        self.raster_types_model = DBItemModel(raster_types)
        self.cboRasterType.setModel(self.raster_types_model)

        if is_context is True:
            #     # Select and lock in the rsater type for basemaps
            #     self.cboRasterType.setEnabled(False)
            #     basemap_raster_type = self.raster_types_model.getItemIndexById(RASTER_TYPE_BASEMAP)
            #     self.cboRasterType.setCurrentIndex(basemap_raster_type)

            self.setWindowTitle('Create New Context Raster' if self.raster is None else 'Edit Context Raster Properties')
        # else:
            self.setWindowTitle('Create New Surface Raster' if self.raster is None else 'Edit Surface Raster Properties')

        if raster is None:
            self.txtName.textChanged.connect(self.on_name_changed)
            self.txtSourcePath.textChanged.connect(self.on_name_changed)
            self.txtSourcePath.setText(import_source_path)
            self.txtName.setText(os.path.splitext(os.path.basename(import_source_path))[0])

            # Masks (filtered to just AOI)
            self.masks = {id: mask for id, mask in self.project.masks.items() if mask.mask_type.id == AOI_MASK_TYPE_ID}
            no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
            self.masks[0] = no_clipping
            self.masks_model = DBItemModel(self.masks)
            self.cboMask.setModel(self.masks_model)
            # Default to no mask clipping
            self.cboMask.setCurrentIndex(self.masks_model.getItemIndex(no_clipping))
            self.cboRasterType.currentIndexChanged.connect(self.set_hillshade)
        else:
            self.txtName.setText(raster.name)
            self.txtDescription.setPlainText(raster.description)

            self.lblSourcePath.setVisible(False)
            self.txtSourcePath.setVisible(False)
            self.lblMask.setVisible(False)
            self.cboMask.setVisible(False)
            self.chkHillshade.setChecked(False)
            self.chkHillshade.setVisible(False)

            self.txtProjectPath.setText(project.get_absolute_path(raster.path))

            self.chkAddToMap.setVisible(False)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)

        self.txtName.selectAll()

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if self.raster is not None:
            try:
                self.raster.update(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
                # TODO update hillshade if exists
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A raster with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving raster', str(ex))
                return

            super(FrmRaster, self).accept()

        else:
            # Inserting a new raster. Check name uniqueness before copying the raster file
            if validate_name_unique(self.project.project_file, 'rasters', 'name', self.txtName.text()) is False:
                QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A raster with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                self.txtName.setFocus()
                return

            try:
                mask = self.cboMask.currentData(QtCore.Qt.UserRole)
                mask_tuple = (self.project.project_file, mask.id) if mask.id > 0 else None

                project_path = self.project.get_absolute_path(self.txtProjectPath.text())

                if not os.path.isdir(os.path.dirname(project_path)):
                    os.makedirs(os.path.dirname(project_path))

                copy_raster = CopyRaster(self.txtSourcePath.text(), mask_tuple, project_path)

                self.buttonBox.setEnabled(False)

                if self.chkHillshade.isChecked() is True:
                    self.hillshade_raster_name = f'{self.txtName.text()} hillshade'
                    hillshade_path = self.project.get_absolute_path(self.hillshade_project_path)
                    hillshade_task = Hillshade(project_path, hillshade_path)
                    hillshade_task.addSubTask(copy_raster, [], QgsTask.ParentDependsOnSubTask)
                    hillshade_task.hillshade_complete.connect(self.on_raster_copy_complete)
                    QgsApplication.taskManager().addTask(hillshade_task)
                else:
                    copy_raster.copy_raster_complete.connect(self.on_raster_copy_complete)
                    QgsApplication.taskManager().addTask(copy_raster)

                # Call the run command directly during development to run the process synchronousely.
                # DO NOT DEPLOY WITH run() UNCOMMENTED
                # copy_raster.run()

            except Exception as ex:
                self.buttonBox.setEnabled(True)

                try:
                    self.raster.delete(self.project.project_file)
                except Exception as ex2:
                    QgsMessageLog.logMessage(f'Error attempting to delete raster after the importing raster failed.\n{ex2}', 'Copy Raster', Qgis.Critical)
                self.raster = None
                QtWidgets.QMessageBox.warning(self, 'Error Importing raster', str(ex))
                return

    @pyqtSlot(bool)
    def on_raster_copy_complete(self, result: bool):

        if result is True:
            self.iface.messageBar().pushMessage('Raster Copy Complete.', f'Raster {self.txtName.text()} added to project', level=Qgis.Info, duration=5)

            try:
                raster_type = self.cboRasterType.currentData(QtCore.Qt.UserRole).id

                self.raster = insert_raster(self.project.project_file, self.txtName.text(), self.txtProjectPath.text(), raster_type, self.txtDescription.toPlainText(), self.is_context)
                self.project.rasters[self.raster.id] = self.raster
                if self.chkHillshade.isChecked() is True:
                    hillshade_metadata = {'parent_raster': self.raster.name, 'parent_raster_id': self.raster.id}
                    self.hillshade = insert_raster(self.project.project_file, self.hillshade_raster_name, self.hillshade_project_path, 6, self.txtDescription.toPlainText(), self.is_context, metadata=hillshade_metadata)
                    self.project.rasters[hillshade.id] = hillshade
                    raster_metadata = {'hillsahde_raster': self.hillshade_project_path, 'hillshade_raster_id': hillshade.id}
                    self.raster.update(self.project.project_file, self.raster.name, self.raster.description, metadata=raster_metadata)

            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A raster with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Raster', str(ex))
                return

            super(FrmRaster, self).accept()
        else:
            self.iface.messageBar().pushMessage('Raster Copy Error', 'Review the QGIS log.', level=Qgis.Critical, duration=5)
            try:
                self.raster.delete(self.project.project_file)
            except Exception as ex:
                QgsMessageLog.logMessage(f'Error attempting to delete raster after the importing raster failed.: {ex}', 'QRiS_CopyRaster Task', Qgis.Critical)
            self.raster = None

            self.buttonBox.setEnabled(True)

    def on_name_changed(self, new_name):
        project_name = self.txtName.text().strip()
        clean_name = ''.join(e for e in project_name.replace(" ", "_") if e.isalnum() or e == "_")
        clean_name_hillshade = f'{clean_name}_hillshade'

        if len(project_name) > 0:
            _name, ext = os.path.splitext(self.txtSourcePath.text())
            parent_folder = CONTEXT_PARENT_FOLDER if self.is_context else SURFACES_PARENT_FOLDER
            self.txtProjectPath.setText(os.path.join(parent_folder, self.project.get_safe_file_name(clean_name, ext)))
            self.hillshade_project_path = os.path.join(parent_folder, self.project.get_safe_file_name(clean_name_hillshade, ext))
        else:
            self.txtProjectPath.setText('')
            self.hillshade_project_path = None

    def set_hillshade(self):
        """check hillshade if raster type is dem"""
        raster = self.cboRasterType.currentData(QtCore.Qt.UserRole)
        if raster.id == 4:
            self.chkHillshade.setEnabled(True)
            self.chkHillshade.setChecked(True)
        else:
            self.chkHillshade.setEnabled(False)
            self.chkHillshade.setChecked(False)

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblSourcePath = QtWidgets.QLabel()
        self.lblSourcePath.setText('Source Path')
        self.grid.addWidget(self.lblSourcePath, 1, 0, 1, 1)

        self.txtSourcePath = QtWidgets.QLineEdit()
        self.txtSourcePath.setReadOnly(True)
        self.grid.addWidget(self.txtSourcePath, 1, 1, 1, 1)

        self.lblRasterType = QtWidgets.QLabel()
        self.lblRasterType.setText('Raster Type')
        self.grid.addWidget(self.lblRasterType, 2, 0, 1, 1)

        self.cboRasterType = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboRasterType, 2, 1, 1, 1)

        self.lblProjectPath = QtWidgets.QLabel()
        self.lblProjectPath.setText('Project Path')
        self.grid.addWidget(self.lblProjectPath, 3, 0, 1, 1)

        self.txtProjectPath = QtWidgets.QLineEdit()
        self.txtProjectPath.setReadOnly(True)
        self.grid.addWidget(self.txtProjectPath, 3, 1, 1, 1)

        self.lblMask = QtWidgets.QLabel()
        self.lblMask.setText('Clip to AOI')
        self.grid.addWidget(self.lblMask, 4, 0, 1, 1)

        self.cboMask = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboMask, 4, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel()
        self.lblDescription.setText('Description')
        self.grid.addWidget(self.lblDescription, 5, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription, 5, 1, 1, 1)

        self.chkHillshade = QtWidgets.QCheckBox('Create Hillshade')
        self.chkHillshade.setChecked(False)
        self.chkHillshade.setEnabled(False)
        self.grid.addWidget(self.chkHillshade, 6, 1, 1, 1)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setText('Add to Map')
        self.chkAddToMap.setChecked(True)
        self.grid.addWidget(self.chkAddToMap, 7, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'basemaps'))
