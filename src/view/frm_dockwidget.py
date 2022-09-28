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
from osgeo import ogr
from qgis.core import QgsMapLayer, QgsApplication, Qgis, QgsWkbTypes
from qgis.utils import iface
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.gui import QgsMapToolEmitPoint
from PyQt5.QtCore import pyqtSlot

from ..model.scratch_vector import ScratchVector, scratch_gpkg_path
from ..model.layer import Layer
from ..model.project import Project
from ..model.event import Event
from ..model.event import EVENT_MACHINE_CODE
from ..model.basemap import BASEMAP_MACHINE_CODE, PROTOCOL_BASEMAP_MACHINE_CODE, RASTER_TYPE_BASEMAP, Raster
from ..model.mask import MASK_MACHINE_CODE
from ..model.analysis import ANALYSIS_MACHINE_CODE, Analysis
from ..model.db_item import DB_MODE_CREATE, DB_MODE_IMPORT, DBItem
from ..model.event import EVENT_MACHINE_CODE, Event
from ..model.basemap import BASEMAP_MACHINE_CODE, Raster
from ..model.mask import MASK_MACHINE_CODE, Mask, REGULAR_MASK_TYPE_ID, AOI_MASK_TYPE_ID, DIRECTIONAL_MASK_TYPE_ID
from ..model.protocol import Protocol
from ..model.pour_point import PourPoint, CONTEXT_NODE_TAG

from .frm_design2 import FrmDesign
from .frm_event import DATA_CAPTURE_EVENT_TYPE_ID
from .frm_event import FrmEvent
from .frm_basemap import FrmRaster
from .frm_mask_aoi import FrmMaskAOI
from .frm_analysis_properties import FrmAnalysisProperties
from .frm_new_project import FrmNewProject
from .frm_pour_point import FrmPourPoint
from .frm_analysis_docwidget import FrmAnalysisDocWidget
from .frm_slider import FrmSlider
from .frm_scratch_vector import FrmScratchVector

from ..QRiS.settings import Settings
from ..QRiS.method_to_map import build_basemap_layer, remove_db_item_layer, check_for_existing_layer, build_scratch_vector
from ..QRiS.method_to_map import build_event_protocol_single_layer, build_basemap_layer, build_mask_layer, build_pour_point_map_layer

from ..gp.feature_class_functions import browse_raster, browse_vector
from ..gp.stream_stats import transform_geometry, get_state_from_coordinates
from ..gp.stream_stats import StreamStats
from ..gp.metrics_task import MetricsTask

SCRATCH_NODE_TAG = 'SCRATCH'

# Name of the icon PNG file used for group folders in the QRiS project tree
# /Images/folder.png
FOLDER_ICON = 'folder'

# These are the labels used for displaying the group nodes in the QRiS project tree
GROUP_FOLDER_LABELS = {
    EVENT_MACHINE_CODE: 'Data Capture Events',
    BASEMAP_MACHINE_CODE: 'Basemaps',
    MASK_MACHINE_CODE: 'Masks',
    PROTOCOL_BASEMAP_MACHINE_CODE: 'Basemaps',
    ANALYSIS_MACHINE_CODE: 'Analyses',
    CONTEXT_NODE_TAG: 'Context',
    SCRATCH_NODE_TAG: 'Scratch'
}


class QRiSDockWidget(QtWidgets.QDockWidget):

    closingPlugin = QtCore.pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(QRiSDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # widgets-and-dialogs-with-auto-connect
        self.setupUi()
        self.iface = iface

        self.settings = Settings()

        self.qris_project = None
        self.menu = QtWidgets.QMenu()

        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        # self.treeView.doubleClicked.connect(self.default_tree_action)
        # self.treeView.clicked.connect(self.item_change)
        # self.treeView.expanded.connect(self.expand_tree_item)

        self.model = QtGui.QStandardItemModel()
        self.treeView.setModel(self.model)

        self.analysis_doc_widget = None
        self.slider_doc_widget = None

        self.stream_stats_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.stream_stats_tool.canvasClicked.connect(self.stream_stats_action)

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
        [self.add_child_to_project_tree(basemaps_node, item) for item in self.project.basemaps().values()]

        masks_node = self.add_child_to_project_tree(project_node, MASK_MACHINE_CODE)
        [self.add_child_to_project_tree(masks_node, item) for item in self.project.masks.values()]

        context_node = self.add_child_to_project_tree(project_node, CONTEXT_NODE_TAG)
        [self.add_child_to_project_tree(context_node, item) for item in self.project.pour_points.values()]

        analyses_node = self.add_child_to_project_tree(project_node, ANALYSIS_MACHINE_CODE)
        [self.add_child_to_project_tree(analyses_node, item) for item in self.project.analyses.values()]

        scratch_node = self.add_child_to_project_tree(project_node, SCRATCH_NODE_TAG)
        [self.add_child_to_project_tree(scratch_node, item) for item in self.project.scratch_rasters().values()]
        [self.add_child_to_project_tree(scratch_node, item) for item in self.project.scratch_vectors.values()]

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
        model_data = model_item.data(QtCore.Qt.UserRole)

        if isinstance(model_data, str):
            if model_data == ANALYSIS_MACHINE_CODE:
                self.add_context_menu_item(self.menu, 'Create New Analysis', 'new', lambda: self.add_analysis(model_item))
            else:
                self.add_context_menu_item(self.menu, 'Add To Map', 'add_to_map', lambda: self.add_tree_group_to_map(model_item))
                if model_data == EVENT_MACHINE_CODE:
                    self.add_context_menu_item(self.menu, 'Add New Data Capture Event', 'new', lambda: self.add_event(model_item, DATA_CAPTURE_EVENT_TYPE_ID))
                    self.add_context_menu_item(self.menu, 'Add New Design', 'new', lambda: self.add_event(model_item, 0))
                elif model_data == BASEMAP_MACHINE_CODE:
                    self.add_context_menu_item(self.menu, 'Import Existing Basemap Dataset', 'new', lambda: self.add_basemap(model_item, RASTER_TYPE_BASEMAP))
                elif model_data == MASK_MACHINE_CODE:
                    add_mask_menu = self.menu.addMenu('Create New')
                    self.add_context_menu_item(add_mask_menu, 'Area of Interest', 'new', lambda: self.add_mask(model_item, AOI_MASK_TYPE_ID, DB_MODE_CREATE))
                    self.add_context_menu_item(add_mask_menu, 'Regular Masks', 'new', lambda: self.add_mask(model_item, REGULAR_MASK_TYPE_ID, DB_MODE_CREATE))
                    self.add_context_menu_item(add_mask_menu, 'Directional Masks', 'new', lambda: self.add_mask(model_item, DIRECTIONAL_MASK_TYPE_ID, DB_MODE_CREATE), False)

                    import_mask_menu = self.menu.addMenu('Import Existing')
                    self.add_context_menu_item(import_mask_menu, 'Area of Interest', 'new', lambda: self.add_mask(model_item, AOI_MASK_TYPE_ID, DB_MODE_IMPORT))
                    self.add_context_menu_item(import_mask_menu, 'Regular Masks', 'new', lambda: self.add_mask(model_item, REGULAR_MASK_TYPE_ID, DB_MODE_IMPORT))
                    self.add_context_menu_item(import_mask_menu, 'Directional Masks', 'new', lambda: self.add_mask(model_item, DIRECTIONAL_MASK_TYPE_ID, DB_MODE_IMPORT), False)
                elif model_data == CONTEXT_NODE_TAG:
                    self.add_context_menu_item(self.menu, 'Run USGS StreamStats (US Only)', 'new', lambda: self.add_pour_point(model_item))
                elif model_data == SCRATCH_NODE_TAG:
                    self.add_context_menu_item(self.menu, 'Browse Scratch Space', 'folder', lambda: self.browse_item(model_data, os.path.dirname(scratch_gpkg_path(self.project.project_file))))
                    self.add_context_menu_item(self.menu, 'Import Existing Scratch Raster', 'new', lambda: self.add_basemap(model_item, -1))
                    self.add_context_menu_item(self.menu, 'Import Existing Scratch Vector Feature Class', 'new', lambda: self.add_scratch_vector(model_item))

                    # self.add_context_menu_item(self.menu, 'Create New Empty Mask', 'new', lambda: self.add_mask(model_item, DB_MODE_CREATE))
                    # self.add_context_menu_item(self.menu, 'Import Existing Mask Feature Class', 'new', lambda: self.add_mask(model_item, DB_MODE_IMPORT))
                else:
                    f'Unhandled group folder clicked in QRiS project tree: {model_data}'
        else:
            if isinstance(model_data, DBItem):
                self.add_context_menu_item(self.menu, 'Add To Map', 'add_to_map', lambda: self.add_db_item_to_map(model_item, model_data))
            else:
                raise Exception('Unhandled group folder clicked in QRiS project tree: {}'.format(model_data))

            if isinstance(model_data, Project) \
                    or isinstance(model_data, Event) \
                    or isinstance(model_data, Raster) \
                    or isinstance(model_data, Mask) \
                    or isinstance(model_data, PourPoint) \
                    or isinstance(model_data, Analysis):
                self.add_context_menu_item(self.menu, 'Edit', 'options', lambda: self.edit_item(model_item, model_data))

            if isinstance(model_data, Mask):
                self.add_context_menu_item(self.menu, 'Geospatial Summary', 'gis', lambda: self.geospatial_summary(model_item, model_data))

            if isinstance(model_data, Raster) and model_data.raster_type_id != RASTER_TYPE_BASEMAP:
                self.add_context_menu_item(self.menu, 'Raster Slider', 'slider', lambda: self.raster_slider(model_data))

            if isinstance(model_data, Project):
                self.add_context_menu_item(self.menu, 'Browse Containing Folder', 'folder', lambda: self.browse_item(model_data, os.path.dirname(self.project.project_file)))
            else:
                self.add_context_menu_item(self.menu, 'Delete', 'delete', lambda: self.delete_item(model_item, model_data))

        self.menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def add_context_menu_item(self, menu: QtWidgets.QMenu, menu_item_text: str, icon_file_name, slot: QtCore.pyqtSlot = None, enabled=True):
        action = menu.addAction(QtGui.QIcon(f':/plugins/qris_toolbar/{icon_file_name}'), menu_item_text)
        action.setEnabled(enabled)

        if slot is not None:
            action.triggered.connect(slot)

    def add_db_item_to_map(self, tree_node: QtGui.QStandardItem, db_item: DBItem):

        if isinstance(db_item, Mask):
            build_mask_layer(self.project, db_item)
        elif isinstance(db_item, Raster):
            build_basemap_layer(self.project, db_item)
        elif isinstance(db_item, Event):
            [build_event_protocol_single_layer(self.project, event_layer) for event_layer in db_item.event_layers]
        elif isinstance(db_item, Protocol):
            # determine parent node
            event_node = tree_node.parent()
            event = event_node.data(QtCore.Qt.UserRole)
            for event_layer in event.event_layers:
                if event_layer.layer in db_item.layers:
                    build_event_protocol_single_layer(self.project, event_layer)
        elif isinstance(db_item, Layer):
            # determine parent node
            event_node = tree_node.parent().parent()
            event = event_node.data(QtCore.Qt.UserRole)
            for event_layer in event.event_layers:
                if event_layer.layer == db_item:
                    build_event_protocol_single_layer(self.project, event_layer)
        elif isinstance(db_item, Project):
            [build_mask_layer(mask) for mask in self.project.masks.values()]
            [build_basemap_layer(db_item, basemap) for basemap in self.project.basemaps().values()]
            [[build_event_protocol_single_layer(self.project, event_layer) for event_layer in event.event_layers] for event in self.project.events.values()]
        elif isinstance(db_item, PourPoint):
            build_pour_point_map_layer(self.project, db_item)
        elif isinstance(db_item, ScratchVector):
            build_scratch_vector(self.project, db_item)

    def add_tree_group_to_map(self, model_item: QtGui.QStandardItem):
        """Add all children of a group node to the map ToC
        """

        for row in range(0, model_item.rowCount()):
            child_item = model_item.child(row)
            self.add_db_item_to_map(child_item, child_item.data(QtCore.Qt.UserRole))

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

    def add_analysis(self, parent_node):

        frm = FrmAnalysisProperties(self, self.project)
        result = frm.exec_()
        if result is not None and result != 0:
            self.add_child_to_project_tree(parent_node, frm.analysis, True)

            if self.analysis_doc_widget is None:
                self.analysis_doc_widget = FrmAnalysisDocWidget()
                self.iface.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.analysis_doc_widget)

            self.analysis_doc_widget.configure_analysis(self.project, frm.analysis, None)
            self.analysis_doc_widget.show()

    def raster_slider(self, db_item: DBItem):

        if self.slider_doc_widget is None:
            self.slider_doc_widget = FrmSlider(self, self.project)
            self.iface.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.slider_doc_widget)

        self.slider_doc_widget.configure_raster(db_item)
        self.slider_doc_widget.show()

    def add_child_to_project_tree(self, parent_node: QtGui.QStandardItem, data_item, add_to_map: bool = False) -> QtGui.QStandardItem:
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
            if child_node.data(QtCore.Qt.UserRole) == data_item:
                target_node = child_node
                break

        # Create a new node if none found, or ensure the existing node has the latest name
        if target_node is None:
            icon = FOLDER_ICON
            target_node = QtGui.QStandardItem(data_item.name if isinstance(data_item, DBItem) else GROUP_FOLDER_LABELS[data_item])
            target_node.setIcon(QtGui.QIcon(f':plugins/qris_toolbar/{data_item.icon if isinstance(data_item, DBItem) else FOLDER_ICON}'))
            target_node.setData(data_item, QtCore.Qt.UserRole)
            parent_node.appendRow(target_node)

            if add_to_map is True and isinstance(data_item, DBItem):
                self.add_db_item_to_map(target_node, data_item)

        elif isinstance(data_item, DBItem):
            target_node.setText(data_item.name)

            # Check if the item is in the map and update its name if it is
            check_for_existing_layer(self.project, data_item, add_to_map)

        return target_node

    def add_event_to_project_tree(self, parent_node: QtGui.QStandardItem, event: Event, add_to_map: bool = False):
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

    def add_basemap(self, parent_node: QtGui.QStandardItem, raster_type_id: int):
        """Initiates adding a new base map to the project"""

        import_source_path = browse_raster(self, 'Select a raster dataset to import.')
        if import_source_path is None:
            return

        frm = FrmRaster(self, self.iface, self.project, import_source_path, raster_type_id)
        result = frm.exec_()
        if result != 0:
            self.add_child_to_project_tree(parent_node, frm.raster, frm.chkAddToMap.isChecked())

    def add_scratch_vector(self, parent_node: QtGui.QStandardItem):

        import_source_path = browse_vector(self, 'Select a vector feature class to import.', None)
        if import_source_path is None:
            return

        frm = FrmScratchVector(self, self.iface, self.project, import_source_path, None, None)
        result = frm.exec_()
        if result != 0:
            self.add_child_to_project_tree(parent_node, frm.scratch_vector, frm.chkAddToMap.isChecked())

    def add_mask(self, parent_node: QtGui.QStandardItem, mask_type_id: int, mode: int):
        """Initiates adding a new mask"""

        import_source_path = None
        if mode == DB_MODE_IMPORT:
            import_source_path = browse_vector(self, 'Select a polygon dataset to import as a new mask.', QgsWkbTypes.GeometryType.PolygonGeometry)
            if import_source_path is None:
                return

        frm = FrmMaskAOI(self, self.project, import_source_path, self.project.lookup_tables['lkp_mask_types'][mask_type_id])
        result = frm.exec_()
        if result != 0:
            self.add_child_to_project_tree(parent_node, frm.mask, frm.chkAddToMap.isChecked())

    def add_pour_point(self, parent_node):

        QtWidgets.QMessageBox.information(self, 'Pour Point', 'Click on the map at the location of the desired pour point.' +
                                          '  Be sure to click on the precise stream location.' +
                                          '  A form will appear where you can provide a name and description for the point.' +
                                          '  After you click OK, the pour point location will be transmitted to Stream Stats.'
                                          '  This process can take from a few seconds to a few minutes depending on the size of the catchment.')

        canvas = self.iface.mapCanvas()
        canvas.setMapTool(self.stream_stats_tool)

    def stream_stats_action(self, raw_map_point, button):

        # Revert the default tool so the user doesn't accidentally click again
        self.iface.actionPan().trigger()

        transformed_point = transform_geometry(raw_map_point, self.iface.mapCanvas().mapSettings().destinationCrs().authid(), 4326)

        try:
            state_code = get_state_from_coordinates(transformed_point.y(), transformed_point.x())
            if state_code is None:
                QtWidgets.QMessageBox.warning(self, 'Invalid Location', 'This is a service by USGS and is only available in some US States. See https://streamstats.usgs.gov/ss/ for more information.')
                return
        except Exception as ex:
            QtWidgets.QMessageBox.warning(self, 'Error Determining US State', str(ex))
            return

        frm = FrmPourPoint(self, self.project, transformed_point.y(), transformed_point.x(), None)
        result = frm.exec_()
        if result != 0:
            stream_stats = StreamStats(self.project.project_file,
                                       transformed_point.y(),
                                       transformed_point.x(),
                                       frm.txtName.text(),
                                       frm.txtDescription.toPlainText(),
                                       frm.chkBasin.isChecked(),
                                       frm.chkFlowStats.isChecked(),
                                       frm.chkAddToMap.isChecked())

            stream_stats.stream_stats_successfully_complete.connect(self.stream_stats_complete)

            # Call the run command directly during development to run the process synchronousely.
            # DO NOT DEPLOY WITH run() UNCOMMENTED
            # stream_stats.run()

            # Call the addTask() method to run the process asynchronously. Deploy with this method uncommented.
            QgsApplication.taskManager().addTask(stream_stats)

    @pyqtSlot(PourPoint or None, bool)
    def stream_stats_complete(self, pour_point: PourPoint, add_to_map: bool):

        if isinstance(pour_point, PourPoint):
            self.iface.messageBar().pushMessage('Stream Stats Complete', f'Catchment delineation successful for {pour_point.name}.', level=Qgis.Info, duration=5)
            self.project.pour_points[pour_point.id] = pour_point

            rootNode = self.model.invisibleRootItem()
            project_node = self.add_child_to_project_tree(rootNode, self.project)
            context_node = self.add_child_to_project_tree(project_node, CONTEXT_NODE_TAG)
            self.add_child_to_project_tree(context_node, pour_point, add_to_map)

        else:
            self.iface.messageBar().pushMessage('Stream Stats Error', 'Check the QGIS Log for details.', level=Qgis.Warning, duration=5)

    def edit_item(self, model_item: QtGui.QStandardItem, db_item: DBItem):

        frm = None
        if isinstance(db_item, Project):
            frm = FrmNewProject(os.path.dirname(db_item.project_file), parent=self, project=db_item)
        elif isinstance(db_item, Event):
            if db_item.event_type.id == DATA_CAPTURE_EVENT_TYPE_ID:
                frm = FrmEvent(self, self.project, event=db_item)
            else:
                frm = FrmDesign(self, self.project, db_item)
        elif isinstance(db_item, Mask):
            frm = FrmMaskAOI(self, self.project, None, db_item.mask_type, db_item)
        elif isinstance(db_item, Raster):
            frm = FrmRaster(self, self.iface, self.project, None, db_item.raster_type_id, db_item)
        elif isinstance(db_item, PourPoint):
            frm = FrmPourPoint(self, self.project, db_item.latitude, db_item.longitude, db_item)
        elif isinstance(db_item, Analysis):
            if self.analysis_doc_widget is None:
                self.analysis_doc_widget = FrmAnalysisDocWidget()
                self.iface.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.analysis_doc_widget)
            self.analysis_doc_widget.configure_analysis(self.project, db_item, None)
            self.analysis_doc_widget.show()
        else:
            QtWidgets.QMessageBox.warning(self, 'Delete', 'Editing items is not yet implemented.')

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

    def geospatial_summary(self, model_item, model_data: Mask):

        task = MetricsTask(self.project, model_data)
        task.run()

    def delete_item(self, model_item: QtGui.QStandardItem, db_item: DBItem):

        response = QtWidgets.QMessageBox.question(self, 'Confirm Delete', 'Are you sure that you want to delete the selected item?')
        if response == QtWidgets.QMessageBox.No:
            return

        # Remove the layer from the map first
        remove_db_item_layer(self.project, db_item)

        # Remove the item from the project tree
        model_item.parent().removeRow(model_item.row())

        # Remove the item from the project
        self.project.remove(db_item)

        # Delete the item from the database
        db_item.delete(self.project.project_file)

    def browse_item(self, db_item: DBItem, folder_path):

        # folder_path = None
        # if isinstance(db_item, Raster):
        #     folder_path = os.path.join(os.path.dirname(self.project.project_file), db_item.path)
        # else:
        #     folder_path = self.project.project_file

        # while not os.path.isdir(folder_path):
        #     folder_path = os.path.dirname(folder_path)

        qurl = QtCore.QUrl.fromLocalFile(folder_path)
        QtGui.QDesktopServices.openUrl(qurl)

    def setupUi(self):

        self.setWindowTitle('QRiS Plugin')

        self.resize(489, 536)
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.treeView = QtWidgets.QTreeView(self.dockWidgetContents)
        self.treeView.setSortingEnabled(True)
        self.treeView.setHeaderHidden(True)
        self.treeView.setObjectName("treeView")
        self.treeView.header().setSortIndicatorShown(False)
        self.gridLayout.addWidget(self.treeView, 0, 0, 1, 1)
        self.setWidget(self.dockWidgetContents)
