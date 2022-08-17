# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QRiSDockWidget
                                 A QGIS plugin
 QGIS Riverscapes Studio (QRiS)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-05-06
        git sha              : $Format:%H$
        copyright            : (C) 2021 by North Arrow Research
        email                : info@northarrowresearch.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from xmlrpc.client import Boolean

from qgis.core import QgsMapLayer
from qgis.gui import QgsDataSourceSelectDialog
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QAbstractItemView, QFileDialog, QMenu, QMessageBox, QDockWidget
from qgis.PyQt.QtCore import pyqtSignal, Qt, QDate, pyqtSlot, QUrl
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QIcon, QDesktopServices

from ..model.layer import Layer
from ..model.project import Project
from ..model.event import Event
from ..model.event import EVENT_MACHINE_CODE
from ..model.basemap import BASEMAP_MACHINE_CODE, PROTOCOL_BASEMAP_MACHINE_CODE, Basemap
from ..model.mask import MASK_MACHINE_CODE
from ..model.analysis import ANALYSIS_MACHINE_CODE, Analysis
from ..model.db_item import DB_MODE_CREATE, DB_MODE_IMPORT, DBItem
from ..model.event import EVENT_MACHINE_CODE, Event
from ..model.basemap import BASEMAP_MACHINE_CODE, Basemap
from ..model.mask import MASK_MACHINE_CODE, Mask
from ..model.protocol import Protocol

from .frm_design2 import FrmDesign
from .frm_event import DATA_CAPTURE_EVENT_TYPE_ID
from .frm_event import FrmEvent
from .frm_basemap import FrmBasemap
from .frm_mask_aoi import FrmMaskAOI
from .frm_new_analysis import FrmNewAnalysis
from .frm_new_project import FrmNewProject

from ..QRiS.settings import Settings
from ..QRiS.method_to_map import build_basemap_layer, get_project_group, remove_db_item_layer, check_for_existing_layer
from ..QRiS.method_to_map import build_event_protocol_single_layer, build_basemap_layer, build_mask_layer

from .ui.qris_dockwidget import Ui_QRiSDockWidget

from ..gp.feature_class_functions import browse_source

SCRATCH_NODE_TAG = 'SCRATCH'

# Name of the icon PNG file used for group folders in the QRiS project tree
# /Images/folder.png
FOLDER_ICON = 'folder'

# These are the labels used for displaying the group nodes in the QRiS project tree
GROUP_FOLDER_LABELS = {
    EVENT_MACHINE_CODE: 'Data Capture Events',
    BASEMAP_MACHINE_CODE: 'Basemaps',
    MASK_MACHINE_CODE: 'Masks',
    PROTOCOL_BASEMAP_MACHINE_CODE: 'Basemaps'
}


class QRiSDockWidget(QDockWidget, Ui_QRiSDockWidget):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(QRiSDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.settings = Settings()

        self.qris_project = None
        self.menu = QMenu()

        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        # self.treeView.doubleClicked.connect(self.default_tree_action)
        # self.treeView.clicked.connect(self.item_change)
        # self.treeView.expanded.connect(self.expand_tree_item)

        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)

    # Take this out of init so that nodes can be added as new data is added and imported;
    def build_tree_view(self, project_file, new_item=None):
        """
        Builds the project tree from scratch for the first time
        """
        self.project = Project(project_file)

        self.model.clear()
        self.tree_state = {}
        rootNode = self.model.invisibleRootItem()

        # set the project root
        project_node = self.add_child_to_project_tree(rootNode, self.project)
        events_node = self.add_child_to_project_tree(project_node, EVENT_MACHINE_CODE)
        [self.add_event_to_project_tree(events_node, item) for item in self.project.events.values()]

        basemaps_node = self.add_child_to_project_tree(project_node, BASEMAP_MACHINE_CODE)
        [self.add_child_to_project_tree(basemaps_node, item) for item in self.project.basemaps.values()]

        masks_node = self.add_child_to_project_tree(project_node, MASK_MACHINE_CODE)
        [self.add_child_to_project_tree(masks_node, item) for item in self.project.masks.values()]

        # scratch_node = self.add_child(project_node, SCRATCH_NODE_TAG, 'BrowseFolder')
        # analyses_node = self.add_child(project_node, ANALYSIS_MACHINE_CODE, 'BrowseFolder')

        self.treeView.expandAll()
        return

    def closeEvent(self, event):
        self.qris_project = None
        self.closingPlugin.emit()
        event.accept()

    def open_menu(self, position):
        """Connects signals as context menus to items in the tree"""
        self.menu.clear()
        indexes = self.treeView.selectedIndexes()
        if len(indexes) < 1:
            return

        # No multiselect so there is only ever one item
        idx = indexes[0]
        if not idx.isValid():
            return

        model_item = self.model.itemFromIndex(indexes[0])
        model_data = model_item.data(Qt.UserRole)

        if isinstance(model_data, str):
            if model_data == ANALYSIS_MACHINE_CODE:
                self.add_context_menu_item(self.menu, 'Create New Analysis', 'new', lambda: self.add_analysis(model_item, DB_MODE_CREATE))
            else:
                self.add_context_menu_item(self.menu, 'Add To Map', 'add_to_map', lambda: self.add_tree_group_to_map(model_item))
                if model_data == EVENT_MACHINE_CODE:
                    self.add_context_menu_item(self.menu, 'Add New Data Capture Event', 'new', lambda: self.add_event(model_item, DATA_CAPTURE_EVENT_TYPE_ID))
                    self.add_context_menu_item(self.menu, 'Add New Design', 'new', lambda: self.add_event(model_item, 0))
                elif model_data == BASEMAP_MACHINE_CODE:
                    self.add_context_menu_item(self.menu, 'Import Existing Basemap Dataset', 'new', lambda: self.add_basemap(model_item))
                elif model_data == MASK_MACHINE_CODE:
                    add_mask_menu = self.menu.addMenu('Create New')
                    self.add_context_menu_item(add_mask_menu, 'Area of Interest', 'new', lambda: self.add_mask(model_item, DB_MODE_CREATE))
                    self.add_context_menu_item(add_mask_menu, 'Regular Masks', 'new', lambda: self.add_mask(model_item, DB_MODE_CREATE), False)
                    self.add_context_menu_item(add_mask_menu, 'Directional Masks', 'new', lambda: self.add_mask(model_item, DB_MODE_CREATE), False)

                    import_mask_menu = self.menu.addMenu('Import Existing')
                    self.add_context_menu_item(import_mask_menu, 'Area of Interest', 'new', lambda: self.add_mask(model_item, DB_MODE_IMPORT))
                    self.add_context_menu_item(import_mask_menu, 'Regular Masks', 'new', lambda: self.add_mask(model_item, DB_MODE_IMPORT), False)
                    self.add_context_menu_item(import_mask_menu, 'Directional Masks', 'new', lambda: self.add_mask(model_item, DB_MODE_IMPORT), False)

                    # self.add_context_menu_item(self.menu, 'Create New Empty Mask', 'new', lambda: self.add_mask(model_item, DB_MODE_CREATE))
                    # self.add_context_menu_item(self.menu, 'Import Existing Mask Feature Class', 'new', lambda: self.add_mask(model_item, DB_MODE_IMPORT))
                else:
                    f'Unhandled group folder clicked in QRiS project tree: {model_data}'
        else:
            if isinstance(model_data, DBItem):
                self.add_context_menu_item(self.menu, 'Add To Map', 'add_to_map', lambda: self.add_db_item_to_map(model_item, model_data))
            else:
                raise Exception('Unhandled group folder clicked in QRiS project tree: {}'.format(model_data))

            if isinstance(model_data, Project) or isinstance(model_data, Event) or isinstance(model_data, Basemap) or isinstance(model_data, Mask):
                self.add_context_menu_item(self.menu, 'Edit', 'options', lambda: self.edit_item(model_item, model_data))

            if isinstance(model_data, Project):
                self.add_context_menu_item(self.menu, 'Browse Containing Folder', 'folder', lambda: self.browse_item(model_data))
            else:
                self.add_context_menu_item(self.menu, 'Delete', 'delete', lambda: self.delete_item(model_item, model_data))

        self.menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def add_context_menu_item(self, menu: QMenu, menu_item_text: str, icon_file_name, slot: pyqtSlot = None, enabled=True):
        action = menu.addAction(QIcon(f':/plugins/qris_toolbar/{icon_file_name}'), menu_item_text)
        action.setEnabled(enabled)

        if slot is not None:
            action.triggered.connect(slot)

    def add_db_item_to_map(self, tree_node: QStandardItem, db_item: DBItem):

        if isinstance(db_item, Mask):
            build_mask_layer(self.project, db_item)
        elif isinstance(db_item, Basemap):
            build_basemap_layer(self.project, db_item)
        elif isinstance(db_item, Event):
            [build_event_protocol_single_layer(self.project, event_layer) for event_layer in db_item.event_layers]
        elif isinstance(db_item, Protocol):
            # determine parent node
            event_node = tree_node.parent()
            event = event_node.data(Qt.UserRole)
            for event_layer in event.event_layers:
                if event_layer.layer in db_item.layers:
                    build_event_protocol_single_layer(self.project, event_layer)
        elif isinstance(db_item, Layer):
            # determine parent node
            event_node = tree_node.parent().parent()
            event = event_node.data(Qt.UserRole)
            for event_layer in event.event_layers:
                if event_layer.layer == db_item:
                    build_event_protocol_single_layer(self.project, event_layer)
        elif isinstance(db_item, Project):
            [build_mask_layer(mask) for mask in self.project.masks.values()]
            [build_basemap_layer(db_item, basemap) for basemap in self.project.basemaps.values()]
            [[build_event_protocol_single_layer(self.project, event_layer) for event_layer in event.event_layers] for event in self.project.events.values()]

    def add_tree_group_to_map(self, model_item: QStandardItem):
        """Add all children of a group node to the map ToC
        """

        for row in range(0, model_item.rowCount()):
            child_item = model_item.child(row)
            self.add_db_item_to_map(child_item, child_item.data(Qt.UserRole))

    def expand_tree(self):
        self.treeView.expandAll()
        return

    def collapse_tree(self):
        self.treeView.collapseAll()
        return

    def add_event(self, parent_node, event_type_id: int):
        """Initiates adding a new data capture event"""
        if event_type_id == DATA_CAPTURE_EVENT_TYPE_ID:
            frm = FrmEvent(self, self.project)
        else:
            frm = FrmDesign(self, self.project)

        # self.assessment_dialog.dateEdit_assessment_date.setDate(QDate.currentDate())
        # self.assessment_dialog.dataChange.connect(self.build_tree_view)
        result = frm.exec_()
        if result is not None and result != 0:
            self.add_event_to_project_tree(parent_node, frm.event, frm.chkAddToMap.isChecked())

    def add_child_to_project_tree(self, parent_node: QStandardItem, data_item, add_to_map: Boolean = False) -> QStandardItem:
        """
        Looks at all child nodes of the parent_node and returns the existing QStandardItem
        that has the DBitem attached. It will also update the existing node with the latest name
        in the event that the data item has just been edited.

        A new node is created if no existing node is found.

        The data_item can either be a DBItem object or a string for group nodes
        """

        # Search for a child node of the parent with the specified data attached
        target_node = None
        for row in range(0, parent_node.rowCount()):
            child_node = parent_node.child(row)
            if child_node.data(Qt.UserRole) == data_item:
                target_node = child_node
                break

        # Create a new node if none found, or ensure the existing node has the latest name
        if target_node is None:
            icon = FOLDER_ICON
            target_node = QStandardItem(data_item.name if isinstance(data_item, DBItem) else GROUP_FOLDER_LABELS[data_item])
            target_node.setIcon(QIcon(f':plugins/qris_toolbar/{data_item.icon if isinstance(data_item, DBItem) else FOLDER_ICON}'))
            target_node.setData(data_item, Qt.UserRole)
            parent_node.appendRow(target_node)

            if add_to_map == True and isinstance(data_item, DBItem):
                self.add_db_item_to_map(target_node, data_item)

        elif isinstance(data_item, DBItem):
            target_node.setText(data_item.name)

            # Check if the item is in the map and update its name if it is
            check_for_existing_layer(self.project, data_item, add_to_map)

        return target_node

    def add_event_to_project_tree(self, parent_node: QStandardItem, event: Event, add_to_map: Boolean = False):
        """
        Most project data types can be added to the project tree using add_child_to_project_tree()
        but data capture events have child nodes so they need this special method.
        """

        # Event, protocols and layers
        event_node = self.add_child_to_project_tree(parent_node, event, add_to_map)
        for protocol in event.protocols:
            protocol_node = self.add_child_to_project_tree(event_node, protocol, add_to_map)
            for layer in protocol.layers:
                if layer.is_lookup is False:
                    self.add_child_to_project_tree(protocol_node, layer, add_to_map)

        # # Basemaps
        # if len(event.basemaps) > 0:
        #     basemap_group_node = self.add_child_to_project_tree(event_node, PROTOCOL_BASEMAP_MACHINE_CODE)
        #     [self.add_child_to_project_tree(basemap_group_node, basemap) for basemap in event.basemaps]

    def add_basemap(self, parent_node: QStandardItem):
        """Initiates adding a new base map to the project"""

        import_source_path = browse_source(self, 'Select a raster dataset to import as a new basis dataset.', QgsMapLayer.RasterLayer)
        if import_source_path is None:
            return

        frm = FrmBasemap(self, self.project, import_source_path)
        result = frm.exec_()
        if result != 0:
            self.add_child_to_project_tree(parent_node, frm.basemap, frm.chkAddToMap.isChecked())

    def add_mask(self, parent_node, mode):
        """Initiates adding a new mask"""

        import_source_path = None
        if mode == DB_MODE_IMPORT:
            import_source_path = browse_source(self, 'Select a polygon dataset to import as a new mask.', QgsMapLayer.VectorLayer)
            if import_source_path is None:
                return

        frm = FrmMaskAOI(self, self.project, import_source_path)
        result = frm.exec_()
        if result != 0:
            self.add_child_to_project_tree(parent_node, frm.mask, frm.chkAddToMap.isChecked())

    def edit_item(self, model_item: QStandardItem, db_item: DBItem):

        frm = None
        if isinstance(db_item, Project):
            frm = FrmNewProject(os.path.dirname(db_item.project_file), parent=self, project=db_item)
        elif isinstance(db_item, Event):
            if db_item.event_type.id == DATA_CAPTURE_EVENT_TYPE_ID:
                frm = FrmEvent(self, self.project, event=db_item)
            else:
                frm = FrmDesign(self, self.project, db_item)
        elif isinstance(db_item, Mask):
            frm = FrmMaskAOI(parent=self, project=self.project, import_source_path=None, mask=db_item)
        elif isinstance(db_item, Basemap):
            frm = FrmBasemap(self, self.project, None, db_item)
        else:
            QMessageBox.warning(self, 'Delete', 'Editing items is not yet implemented.')

        if frm is not None:
            result = frm.exec_()
            if result is not None and result != 0:

                # Adding the item into the tree again will ensure that it's name is up to date
                # and that any child nodes are correct. It will also ensure that the corresponding
                # map table of contents item is renamed.
                if isinstance(db_item, Project):
                    self.add_child_to_project_tree(self.model.invisibleRootItem(), db_item, False)
                elif isinstance(db_item, Event):
                    self.add_event_to_project_tree(model_item.parent(), db_item, frm.chkAddToMap.isChecked())
                else:
                    self.add_child_to_project_tree(model_item.parent(), db_item, frm.chkAddToMap.isChecked())

    def delete_item(self, model_item: QStandardItem, db_item: DBItem):

        response = QMessageBox.question(self, 'Confirm Delete', 'Are you sure that you want to delete the selected item?')
        if response == QMessageBox.No:
            return

        # Remove the layer from the map first
        remove_db_item_layer(self.project, db_item)

        # Remove the item from the project tree
        model_item.parent().removeRow(model_item.row())

        # Remove the item from the project
        self.project.remove(db_item)

        # Delete the item from the database
        db_item.delete(self.project.project_file)

    def browse_item(self, db_item: DBItem):

        folder_path = None
        if isinstance(db_item, Basemap):
            folder_path = os.path.join(os.path.dirname(self.project.project_file), db_item.path)
        else:
            folder_path = self.project.project_file

        while not os.path.isdir(folder_path):
            folder_path = os.path.dirname(folder_path)

        qurl = QUrl.fromLocalFile(folder_path)
        QDesktopServices.openUrl(qurl)

    # def add_structure_type(self):
    #     """Initiates adding a structure type and the structure type dialog"""
    #     # TODO First check if the path to the database exists
    #     design_geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
    #     if os.path.exists(design_geopackage_path):
    #         self.structure_type_dialog = StructureTypeDlg(self.qris_project)
    #         self.structure_type_dialog.dataChange.connect(self.build_tree_view)
    #         self.structure_type_dialog.show()
    #     else:
    #         # TODO move the creation of the design data model so that this isn't necessary
    #         QMessageBox.information(self, "Structure Types", "Please create a new project design before adding structure types")

    # def add_zoi_type(self):
    #     """Initiates adding a zoi type and the zoi type dialog"""
    #     # TODO First check if the path to the database exists
    #     design_geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
    #     if os.path.exists(design_geopackage_path):
    #         self.zoi_type_dialog = ZoiTypeDlg(self.qris_project)
    #         self.zoi_type_dialog.dataChange.connect(self.build_tree_view)
    #         self.zoi_type_dialog.show()
    #     else:
    #         # TODO move the creation of the design data model so that this isn't necessary
    #         QMessageBox.information(self, "Structure Types", "Please create a new project design before adding a new influence type")

    # def add_phase(self):
    #     """Initiates adding a new phase within the phase dialog"""
    #     # TODO First check if the path to the database exists
    #     design_geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
    #     if os.path.exists(design_geopackage_path):
    #         self.phase_dialog = PhaseDlg(self.qris_project)
    #         self.phase_dialog.dataChange.connect(self.build_tree_view)
    #         self.phase_dialog.show()
    #     else:
    #         # TODO move the creation of the design data model so that this isn't necessary
    #         QMessageBox.information(self, "Structure Types", "Please create a new project design before adding phases")

    # This will kick off importing photos
    # def import_photos(self):
    #     pass

    # def add_detrended_raster(self):
    #     # last_browse_path = self.settings.getValue('lastBrowsePath')
    #     # last_dir = os.path.dirname(last_browse_path) if last_browse_path is not None else None
    #     dialog_return = QFileDialog.getOpenFileName(None, "Add Detrended Raster to QRiS project", None, self.tr("Raster Data Sources (*.tif)"))
    #     if dialog_return is not None and dialog_return[0] != "" and os.path.isfile(dialog_return[0]):
    #         self.addDetrendedDlg = AddDetrendedRasterDlg(None, dialog_return[0], self.qris_project)
    #         self.addDetrendedDlg.dataChange.connect(self.build_tree_view)
    #         self.addDetrendedDlg.exec()

    # def import_project_extent_layer(self):
    #     """launches the dialog that supports import of a project extent layer polygon"""
    #     select_layer = QgsDataSourceSelectDialog()
    #     select_layer.exec()
    #     uri = select_layer.uri()
    #     if uri is not None and uri.isValid() and uri.wkbType == 3:
    #         self.project_extent_dialog = ProjectExtentDlg(uri, self.qris_project)
    #         self.project_extent_dialog.dataChange.connect(self.build_tree_view)
    #         self.project_extent_dialog.exec_()
    #     else:
    #         QMessageBox.critical(self, "Invalid Layer", "Please select a valid polygon layer")

    # def create_blank_project_extent(self):
    #     """Adds a blank project extent that will be edited by the user"""
    #     self.project_extent_dialog = ProjectExtentDlg(None, self.qris_project)
    #     self.project_extent_dialog.dataChange.connect(self.build_tree_view)
    #     self.project_extent_dialog.exec_()

    # def update_project_extent(self):
    #     """Renames the project extent layer"""
    #     pass

    # def delete_project_extent(self, selected_item):
    #     """Deletes a project extent layer"""
    #     display_name = selected_item.data(item_code['INSTANCE']).display_name
    #     feature_name = selected_item.data(item_code['INSTANCE']).feature_name
    #     geopackage_path = selected_item.data(item_code['INSTANCE']).geopackage_path(self.qris_project.project_path)

    #     delete_ok = QMessageBox.question(self, f"Delete extent", f"Are you fucking sure you wanna delete the extent layer: {display_name}")
    #     if delete_ok == QMessageBox.Yes:
    #         # remove from the map if it's there
    #         # TODO consider doing this based on the path
    #         for layer in QgsProject.instance().mapLayers().values():
    #             if layer.name() == display_name:
    #                 QgsProject.instance().removeMapLayers([layer.id()])
    #                 iface.mapCanvas().refresh()

    #         # TODO be sure to test whether the table exists first
    #         gdal_delete = gdal.OpenEx(geopackage_path, gdal.OF_UPDATE, allowed_drivers=['GPKG'])
    #         error = gdal_delete.DeleteLayer(feature_name)
    #         gdal_delete.ExecuteSQL('VACUUM')
    #         # TODO remove this from the Extents dictionary that will also remove from promect xml
    #         del(self.qris_project.project_extents[feature_name])
    #         # refresh the project xml
    #         self.qris_project.write_project_xml()
    #         # refresh the tree
    #         self.build_tree_view(self.qris_project, None)
    #     else:
    #         QMessageBox.information(self, "Delete extent", "No layers were deleted")

    # def import_project_layer(self):
    #     """launches a dialog that supports import of project layers that can be clipped to a project extent"""
    #     select_layer = QgsDataSourceSelectDialog()
    #     select_layer.exec()
    #     uri = select_layer.uri()
    #     if uri is not None and uri.isValid():  # and uri.wkbType == 3:
    #         self.project_layer_dialog = ProjectLayerDlg(uri, self.qris_project)
    #         self.project_layer_dialog.dataChange.connect(self.build_tree_view)
    #         self.project_layer_dialog.exec_()
    #     else:
    #         QMessageBox.critical(self, "Invalid Layer", "Please select a valid gis layer")

    # def explore_elevations(self, selected_item):
    #     # raster = selected_item.data(item_code['INSTANCE'])
    #     self.elevation_widget = ElevationDockWidget(raster, self.qris_project)
    #     self.settings.iface.addDockWidget(Qt.LeftDockWidgetArea, self.elevation_widget)
    #     self.elevation_widget.dataChange.connect(self.build_tree_view)
    #     self.elevation_widget.show()
