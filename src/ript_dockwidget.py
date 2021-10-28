# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RIPTDockWidget
                                 A QGIS plugin
 Riverscapes Integrated Planning Tool (RIPT)
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
from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsRasterLayer,
    QgsVectorLayer,
    QgsProject,
    QgsField,
    QgsExpressionContextUtils,
    QgsVectorFileWriter)

from qgis.gui import QgsDataSourceSelectDialog

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtWidgets import QAbstractItemView, QFileDialog
from qgis.PyQt.QtCore import pyqtSignal, Qt, QDate
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QIcon

from .classes.context_menu import ContextMenu
from .ript_elevation_dockwidget import RIPTElevationDockWidget
from .add_detrended_dialog import AddDetrendedRasterDlg
from .add_layer_dialog import AddLayerDlg
from .assessment_dialog import AssessmentDlg
from .classes.settings import Settings

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui', 'ript_dockwidget_base.ui'))

item_code = {'path': Qt.UserRole + 1,
             'item_type': Qt.UserRole + 2,
             'LAYER': Qt.UserRole + 3,
             'map_layer': Qt.UserRole + 4,
             'layer_symbology': Qt.UserRole + 5,
             'feature_id': Qt.UserRole + 6}


class RIPTDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(RIPTDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.settings = Settings()

        self.current_project = None
        self.menu = ContextMenu()

        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        # self.treeView.doubleClicked.connect(self.default_tree_action)
        # self.treeView.clicked.connect(self.item_change)
        # self.treeView.expanded.connect(self.expand_tree_item)

        self.model = QStandardItemModel()
        self.treeView.setModel(self.model)

    def open_project(self, ript_project, new_item=None):
        """Builds items in the tree view based on dictionary values that are part of the project"""
        # TODO resolve this naming - it is stupid and inconsistent throughout
        self.current_project = ript_project

        self.model.clear()
        rootNode = self.model.invisibleRootItem()

        project_node = QStandardItem(ript_project.project_name)
        project_node.setIcon(QIcon(':/plugins/qris_toolbar/RaveAddIn_16px.png'))
        project_node.setData('project_root', item_code['item_type'])
        project_node.setData('group', item_code['map_layer'])
        rootNode.appendRow(project_node)

        # Add detrended rasters to tree
        # TODO refactor using node naming scheme for clarity
        detrended_rasters = QStandardItem("Detrended Rasters")
        detrended_rasters.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        detrended_rasters.setData("DetrendedRastersFolder", item_code['item_type'])
        detrended_rasters.setData('group', item_code['map_layer'])
        project_node.appendRow(detrended_rasters)

        for raster in ript_project.detrended_rasters.values():
            detrended_raster = QStandardItem(raster.name)
            detrended_raster.setIcon(QIcon(':/plugins/qris_toolbar/layers/Raster.png'))
            # detrended_raster.setData(raster.path, item_code['path'])
            detrended_raster.setData('DetrendedRaster', item_code['item_type'])
            detrended_raster.setData(raster, item_code['LAYER'])
            detrended_raster.setData('raster_layer', item_code['map_layer'])
            # detrended_raster.setData(os.path.join(os.path.dirname(__file__), "..", 'resources', 'symbology', 'hand.qml'), item_code['layer_symbology'])
            detrended_rasters.appendRow(detrended_raster)

            if len(raster.surfaces.values()) > 0:
                item_surfaces = QStandardItem("Surfaces")
                item_surfaces.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
                item_surfaces.setData('group', item_code['map_layer'])
                detrended_raster.appendRow(item_surfaces)
                for surface in raster.surfaces.values():
                    item_surface = QStandardItem(surface.name)
                    item_surface.setIcon(QIcon(':/plugins/qris_toolbar/layers/Polygon.png'))
                    # item_surface.setData(surface.path, item_code['path'])
                    item_surface.setData('DetrendedRasterSurface', item_code['item_type'])
                    item_surface.setData('surface_layer', item_code['map_layer'])
                    item_surface.setData(surface, item_code['LAYER'])
                    item_surfaces.appendRow(item_surface)

        # Add project layers to tree
        project_layers = QStandardItem("Project Layers")
        project_layers.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        project_layers.setData('ProjectLayersFolder', item_code['item_type'])
        project_layers.setData('group', item_code['map_layer'])
        project_node.appendRow(project_layers)

        for project_layer in ript_project.project_layers.values():
            layer = QStandardItem(project_layer.name)
            # layer.setData(project_layer.path, item_code['path'])
            layer.setData(project_layer.type, item_code['item_type'])
            layer.setData('project_layer', item_code['map_layer'])
            layer.setData(project_layer, item_code['LAYER'])
            project_layers.appendRow(layer)

        # TODO soft the assessments
        # project_layers.sortChildren(QtAscendingOrder)

        # Add assessments to tree
        assessments_parent_node = QStandardItem("Riverscape Assessments")
        assessments_parent_node.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        assessments_parent_node.setData('AssessmentsFolder', item_code['item_type'])
        assessments_parent_node.setData('group', item_code['map_layer'])
        project_node.appendRow(assessments_parent_node)

        # TODO Loading the tree straight from the layer here
        # TODO make sure to add the FID for each assessment
        if self.current_project.project_assessments:
            assessments_table = QgsVectorLayer(self.current_project.project_assessments_path + "|layername=assessments", "assessments", "ogr")
            for assessment_feature in assessments_table.getFeatures():
                assessment_node = QStandardItem(assessment_feature.attribute('assessment_date').toString('yyyy-MM-dd'))
                assessment_node.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
                assessment_node.setData('dam_assessment', item_code['item_type'])
                assessment_node.setData('assessment_layer', item_code['map_layer'])
                assessment_node.setData(assessment_feature.attribute('fid'), item_code['feature_id'])
                assessments_parent_node.appendRow(assessment_node)

            # Add designs to tree
        design_layers = QStandardItem("Low-Tech Designs")
        design_layers.setIcon(QIcon(':/plugins/qris_toolbar/BrowseFolder.png'))
        design_layers.setData('DesignsFolder', item_code['item_type'])
        project_node.appendRow(design_layers)

        # Check if new item is in the tree, if it is pass it to the new_item function
        if new_item is not None:
            selected_item = self._find_item_in_model(new_item)
            if selected_item is not None:
                self.addToMap(selected_item)

    def closeEvent(self, event):
        self.current_project = None
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

        item = self.model.itemFromIndex(indexes[0])
        # project_tree_data = item.data(Qt.UserRole)  # ProjectTreeData object
        # data = project_tree_data.data  # Could be a QRaveBaseMap, a QRaveMapLayer or just some random data
        # connect signals to treeView menu itemsHmmmm
        item_type = item.data(item_code['item_type'])
        if item_type == 'project_root':
            self.menu.addAction('EXPAND_ALL', lambda: self.expandAll())
        elif item_type == "DetrendedRastersFolder":
            self.menu.addAction('ADD_DETRENDED_RASTER', lambda: self.addDetrendedRasterToProject())
        elif item_type == "DetrendedRaster":
            self.menu.addAction('EXPLORE_ELEVATIONS', lambda: self.exploreElevations(item))
            self.menu.addAction('ADD_TO_MAP', lambda: self.addToMap(item))
        elif item_type in ["DetrendedRasterSurface", 'project_layer', "Project_Extent"]:
            self.menu.addAction('ADD_TO_MAP', lambda: self.addToMap(item))
        elif item_type == "ProjectLayersFolder":
            self.menu.addAction('ADD_PROJECT_LAYER', lambda: self.addLayerToProject())
        elif item_type == "AssessmentsFolder":
            self.menu.addAction('ADD_ASSESSMENT', lambda: self.add_assessment())
        elif item_type == "dam_assessment":
            self.menu.addAction('ADD_TO_MAP', lambda: self.addToMap(item))
        elif item_type == "DesignsFolder":
            self.menu.addAction('ADD_DESIGN', lambda: self.addDesign())
        else:
            self.menu.clear()

        self.menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def addDesign(self):
        pass

    def add_assessment(self):
        """Initiates adding a new assessment"""
        # TODO get consistency among current_project, ript_project, and qris_project
        self.assessment_dialog = AssessmentDlg(self.current_project)
        self.assessment_dialog.dateEdit_assessment_date.setDate(QDate.currentDate())
        self.assessment_dialog.dataChange.connect(self.open_project)
        self.assessment_dialog.show()

    def addDetrendedRasterToProject(self):
        # last_browse_path = self.settings.getValue('lastBrowsePath')
        # last_dir = os.path.dirname(last_browse_path) if last_browse_path is not None else None
        dialog_return = QFileDialog.getOpenFileName(None, "Add Detrended Raster to QRiS project", None, self.tr("Raster Data Sources (*.tif)"))
        if dialog_return is not None and dialog_return[0] != "" and os.path.isfile(dialog_return[0]):
            self.addDetrendedDlg = AddDetrendedRasterDlg(None, dialog_return[0], self.current_project)
            self.addDetrendedDlg.dataChange.connect(self.open_project)
            self.addDetrendedDlg.exec()

    def addLayerToProject(self):
        select_layer = QgsDataSourceSelectDialog()
        select_layer.exec()
        uri = select_layer.uri()
        if uri is not None and uri.isValid():  # check for polygon
            self.addProjectLayerDlg = AddLayerDlg(uri, self.current_project)
            self.addProjectLayerDlg.dataChange.connect(self.open_project)
            self.addProjectLayerDlg.exec_()

    def exploreElevations(self, selected_item):
        raster = selected_item.data(item_code['LAYER'])
        self.elevation_widget = RIPTElevationDockWidget(raster, self.current_project)
        self.settings.iface.addDockWidget(Qt.LeftDockWidgetArea, self.elevation_widget)
        self.elevation_widget.dataChange.connect(self.open_project)
        self.elevation_widget.show()

    def addToMap(self, selected_item):
        """Adds selected items from the QRiS tree to the QGIS layer tree and also to the map"""
        # TODO consider giving node a more explicit name
        node = QgsProject.instance().layerTreeRoot()
        parents = self._get_parents(selected_item)
        parents.append(selected_item)
        # for each parent node
        for item in parents:
            # if has the code group
            if item.data(item_code['map_layer']) == 'group':
                # check if the group is in the qgis layer tree
                if any([c.name() == item.text() for c in node.children()]):
                    # if is set it to the active node
                    node = next(n for n in node.children() if n.name() == item.text())
                else:
                    # if not add the group as a node
                    new_node = node.addGroup(item.text())
                    node = new_node
            # if it's not a group map_layer, but is a raster layer
            elif item.data(item_code['map_layer']) == 'raster_layer':
                # check if the layer text is in the layer tree already
                if not any([c.name() == item.text() for c in node.children()]):
                    # if not start set the raster as a layer
                    layer = QgsRasterLayer(os.path.join(self.current_project.project_path, item.data(item_code['LAYER']).path), item.text())
                    # load a qml for style
                    layer.loadNamedStyle(item.data(item_code['layer_symbology']))
                    QgsProject.instance().addMapLayer(layer, False)
                    node.addLayer(layer)
            elif item.data(item_code['map_layer']) in ['surface_layer', 'project_layer']:
                if not any([c.name() == item.text() for c in node.children()]):
                    layer = QgsVectorLayer(f"{os.path.join(self.current_project.project_path, os.path.dirname(item.data(item_code['LAYER']).path))}|layername={os.path.basename(item.data(item_code['LAYER']).path)}",
                                           item.text(), 'ogr')
                    QgsProject.instance().addMapLayer(layer, False)
                    node.addLayer(layer)
            # for assessment and design layers
            elif item.data(item_code['map_layer'] == 'assessment_layer'):
                # TODO Send to the map with an assessment id for subsetting
                # TODO for now just send the jam layer
                layer = QgsVectorLayer(self.current_project.project_assessments_path + "|layername=dams", "Dams-" + item.text(), "ogr")
                # TODO add a filter with the parent id
                assessment_id = item.data(item_code['feature_id'])
                layer.setSubsetString("assessment_id = " + str(assessment_id))
                QgsExpressionContextUtils.setLayerVariable(layer, 'parent_id', assessment_id)
                # TODO dial in referencing and updating of .qml files
                symbology_path = os.path.join(os.path.dirname(__file__), 'symbology', 'assessments_dams.qml')
                layer.loadNamedStyle(symbology_path)
                # TODO set the variable property for the parent_id
                # TODO connect a .qml with formatting and form properties
                QgsProject.instance().addMapLayer(layer, False)
                node.addLayer(layer)

    def expandAll(self):
        self.treeView.expandAll()
        return

    def _get_parents(self, start_item: QStandardItem):
        """This gets a """
        parents = []
        placeholder = start_item.parent()
        while placeholder is not None and placeholder != self.model.invisibleRootItem():
            parents.append(placeholder)
            placeholder = placeholder.parent()
        parents.reverse()
        return parents

    def _find_item_in_model(self, name):
        """Looks in the tree for an item name passed from the dataChange method."""
        selected_item = self.model.findItems(name, Qt.MatchRecursive)[0]
        return selected_item
