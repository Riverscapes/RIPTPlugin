import os
import importlib

from qgis.PyQt.QtCore import Qt, QObject, pyqtSignal
from qgis.utils import plugins
from qgis.PyQt.QtGui import QStandardItem, QIcon
from qgis.PyQt.QtWidgets import QMenu

from .path_utilities import parse_posix_path

# Try to load these plugin names in priority order
NAMES = ['riverscapes_viewer_dev', 'riverscapes_viewer']


class QRaveIntegration(QObject):

    qrave_to_qris = pyqtSignal(str, str, dict)

    def __init__(self, parent):
        super(QRaveIntegration, self).__init__(parent)
        # from https://gis.stackexchange.com/questions/403501/using-qgis-plugin-from-another-plugin

        self.name = None
        self.plugin_instance = None
        self.symbology_folders = None
        self.qrave_map_layer = None
        self.metric_definitions_folder = None
        self.protocol_folder = None

        # Attemp to find RAVE plugin using lower case names
        plugins_lower_case = {k.lower(): k for k in plugins.keys()}
        rave_names_lower_case = [name.lower() for name in NAMES]
        matched_lower_case_name = next((pname for pname in rave_names_lower_case if pname in plugins_lower_case), None)
        if matched_lower_case_name is not None:

            self.name = plugins_lower_case[matched_lower_case_name]
            self.plugin_instance = plugins[self.name]
            self.qrave_map_layer = importlib.import_module(f'{self.name}.src.classes.qrave_map_layer')
            self.symbology_folders = [parse_posix_path(os.path.join(self.qrave_map_layer.SYMBOLOGY_DIR, 'RiverscapesStudio')),
                                      parse_posix_path(os.path.join(self.qrave_map_layer.SYMBOLOGY_DIR, 'Shared'))]
            self.metric_definitions_folder = parse_posix_path(os.path.join(self.qrave_map_layer.SYMBOLOGY_DIR, '..', 'QRiS', 'metrics'))
            self.protocol_folder = parse_posix_path(os.path.join(self.qrave_map_layer.SYMBOLOGY_DIR, '..', 'QRiS', 'protocols'))

            self.basemaps_module = importlib.import_module(f'{self.name}.src.classes.basemaps')
            self.ProjectTreeData = self.qrave_map_layer.ProjectTreeData
            self.QRaveBaseMap = self.basemaps_module.QRaveBaseMap
            self.BaseMaps = self.basemaps_module.BaseMaps()
            self.BaseMaps.load()

            if self.plugin_instance.dockwidget:
                # Check if the signal is already connected
                if self.plugin_instance.dockwidget.receivers(self.plugin_instance.dockwidget.layerMenuOpen) > 0:
                    self.plugin_instance.dockwidget.layerMenuOpen.disconnect()
                self.plugin_instance.dockwidget.layerMenuOpen.connect(self.qrave_add_to_map_menu_item)

    def qrave_add_to_map_menu_item(self, menu: QMenu, item: QStandardItem, data):
        """Custom menu to show at the bottom of the QRave context menu

        Args:
            menu (_type_): ContextMenu(QMenu) object from QRave
            item (QStandardItem): QStandardItem (PyQt)
            data (ProjectTreeData): ProjectTreeData (QRave)
        """

        menu.addSeparator()
        menu.addCustomAction(QIcon(f':/plugins/qris_toolbar/add_to_map'), "Add to QRiS", lambda: self.add_to_qris(item, data))

    def add_to_qris(self, item: QStandardItem, data):
        """_summary_

        Args:
            item (QStandardItem): QStandardItem (PyQt)
            data (ProjectTreeData): ProjectTreeData (QRave)
        """

        layer = item.data(Qt.UserRole).data
        qrave_project = data.project
        project_meta = qrave_project.meta

        project_source_url = ('None','string')
        if qrave_project.warehouse_meta is not None:
            project_id = qrave_project.warehouse_meta.get('id', None)
            if project_id is not None:
                project_source_url = f'https://data.riverscapes.net/p/{project_id[0]}'
        
        project_meta['SourceUrl'] = (project_source_url, 'string')

        layer_meta = data.data.meta
        out_meta = {'project_metadata': project_meta, 'layer_metadata': layer_meta}
        proj_type = data.project.project_type
        symbology = layer.bl_attr.get('symbology', None)
        if symbology is not None:
            out_meta['symbology'] = os.path.join(proj_type,symbology)
        layer_uri = layer.layer_uri.lower()
        if layer.layer_type == 'raster':
            path = layer.layer_uri
        # check if the layer is a shapefile
        elif layer_uri.endswith('.shp'):
            path = layer.layer_uri
        else:
            path = f'{layer.layer_uri}|layername={layer.layer_name}'
        self.qrave_to_qris.emit(path, layer.layer_type, out_meta)
