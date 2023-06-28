import os
import sqlite3
import json
from textwrap import dedent

from qgis.PyQt.QtGui import QStandardItem, QColor, QColorConstants
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.utils import iface

from ..QRiS.settings import Settings, CONSTANTS

from ..model.db_item import DBItem
from ..model.raster import BASEMAP_MACHINE_CODE

from qgis.core import (
    QgsField,
    QgsLayerTreeGroup,
    QgsLayerTreeNode,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsDefaultValue,
    QgsEditorWidgetSetup,
    QgsProject,
    QgsExpressionContextUtils,
    QgsFieldConstraints,
    QgsColorRampShader,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
    QgsAttributeEditorContainer,
    QgsAttributeEditorField,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsAction,
    QgsAttributeEditorAction,
    QgsMapLayer
)


class RiverscapesMapManager():

    def __init__(self, product_key) -> None:
        super().__init__()
        self.product_key = product_key
        settings = Settings()
        self.symbology_folder = settings.getValue('symbologyDir')
        self.layer_order = ['Basemaps']

    def __get_custom_property(self, project_key: str, db_item: DBItem) -> str:
        return f'{self.product_key}::{project_key}::{db_item.db_table_name}::{db_item.id}'

    def __get_machine_code_custom_property(self, project_key: str, machine_code: str) -> str:
        return f'{self.product_key}::{project_key}::{machine_code}'

    def get_db_item_layer(self, project_key: str, db_item: DBItem, layer: QgsLayerTreeNode) -> QgsLayerTreeNode:

        if layer is None:
            layer = QgsProject.instance().layerTreeRoot()

        target_custom_property = self.__get_custom_property(project_key, db_item)
        layer_custom_property = layer.customProperty(self.product_key)
        if isinstance(layer_custom_property, str) and layer_custom_property == target_custom_property:
            # Ensure it has the latest name (in case this method is called after an edit)
            layer.setName(db_item.name)
            return layer

        if isinstance(layer, QgsLayerTreeGroup):
            for child in layer.children():
                result = self.get_db_item_layer(project_key, db_item, child)
                if isinstance(result, QgsLayerTreeNode):
                    return result

        return None

    # method to get a layer based on its machine code custom property
    def get_machine_code_layer(self, project_key: str, machine_code: str, layer: QgsLayerTreeNode) -> QgsLayerTreeNode:

        if layer is None:
            layer = QgsProject.instance().layerTreeRoot()

        target_custom_property = self.__get_machine_code_custom_property(project_key, machine_code)
        layer_custom_property = layer.customProperty(self.product_key)
        if isinstance(layer_custom_property, str) and layer_custom_property == target_custom_property:
            return layer

        if isinstance(layer, QgsLayerTreeGroup):
            for child in layer.children():
                result = self.get_machine_code_layer(project_key, machine_code, child)
                if isinstance(result, QgsLayerTreeNode):
                    return result

        return None

    def get_group_layer(self, project_key: str, machine_code, group_label, parent: QgsLayerTreeGroup = None, add_missing: bool = False, add_to_bottom=False) -> QgsLayerTreeGroup:
        """
        Finds a group layer directly underneath "parent" with the specified
        machine code as the custom property. No string matching with group
        label is performed.

        When add_missing is True, the group will be created if it can't be found.
        When add_to_bottom is True, the group will be added to the bottom of the parent group.
        """

        if parent is None:
            parent = QgsProject.instance().layerTreeRoot()

        target_custom_property = self.__get_machine_code_custom_property(project_key, machine_code)

        for child_layer in parent.children():
            custom_property = child_layer.customProperty(self.product_key)
            if isinstance(custom_property, str) and custom_property == target_custom_property:
                child_layer.setExpanded(False)
                child_layer.setExpanded(True)
                return child_layer

        if add_missing:

            if add_to_bottom:
                target_index = len(parent.children())
            else:
                target_index = 0
                for group_layer_machine_code in self.layer_order:
                    if group_layer_machine_code == machine_code:
                        break
                    group_index = self.get_group_layer(project_key, group_layer_machine_code, None, parent, False)
                    if group_index is not None:
                        target_index += 1

            group_layer = parent.insertGroup(target_index, group_label)
            group_layer.setCustomProperty(self.product_key, target_custom_property)
            group_layer.setExpanded(False)
            group_layer.setExpanded(True)
            return group_layer

        return None

    def remove_empty_groups(self, group_node: QgsLayerTreeGroup) -> None:

        parent_node = group_node.parent()
        if parent_node is None:
            return

        if len(group_node.children()) < 1:
            parent_node.removeChildNode(group_node)

        if isinstance(parent_node, QgsLayerTreeGroup):
            self.remove_empty_groups(parent_node)

    def remove_db_item_layer(self, project_key: str, db_item: DBItem) -> None:

        layer = self.get_db_item_layer(project_key, db_item, None)
        if layer is not None:
            parent_group = layer.parent()
            parent_group.removeChildNode(layer)
            self.remove_empty_groups(parent_group)

    def remove_machine_code_layer(self, project_key: str, machine_code: str) -> None:

        layer = self.get_machine_code_layer(project_key, machine_code, None)
        if layer is not None:
            parent_group = layer.parent()
            parent_group.removeChildNode(layer)
            self.remove_empty_groups(parent_group)

    def remove_non_basemap_rasters(self, group=None) -> None:
        # recursively search though the root group all groups and layers for raster layers
        # if the raster layer custom property is not a Riverscapes Basemap, remove it

        group = QgsProject.instance().layerTreeRoot() if group is None else group
        for child in group.children():
            if isinstance(child, QgsLayerTreeGroup):
                self.remove_non_basemap_rasters(child)
            else:
                if child.layer().type() == QgsMapLayer.RasterLayer:
                    if child.customProperty('Basemaps') is None:
                        group.removeChildNode(child)

    def test_for_zoom(self) -> bool:
        """Returns True if the map should zoom to the new layer."""

        # get number of layers in the invisible root node do this before we add new layers to the map
        layers = QgsProject.instance().layerTreeRoot().findLayers()
        layer_count = len(layers)
        count_basemaps = len([layer for layer in layers if layer.customProperty('Basemaps') is not None])
        zoom = True if layer_count - count_basemaps == 0 else False

        return zoom

    def create_db_item_feature_layer(self, project_key: str, parent_group: QgsLayerTreeGroup, fc_path: str, db_item: DBItem, id_field: str, symbology_key: str) -> QgsVectorLayer:
        """
        Creates a new feature layer for the specified DBItem and adds it to the map.
        args:
            project_key: The project key
                db_item: The DBItem to create a layer for
                symbology: The symbology to apply to the layer. File name only. No folder or extension."""

        zoom = self.test_for_zoom()

        layer = self.get_db_item_layer(project_key, db_item, None)
        if layer is not None:
            return layer

        # Create a layer from the table
        layer = QgsVectorLayer(fc_path, db_item.name, 'ogr')
        QgsProject.instance().addMapLayer(layer, False)

        # Apply symbology
        symbology_filename = symbology_key if symbology_key.endswith('.qml') else f'{symbology_key}.qml'
        qml = os.path.join(self.symbology_folder, symbology_filename)
        layer.loadNamedStyle(qml)

        if id_field is not None:
            id_value = db_item.event_id if id_field == 'event_id' else db_item.id
            # Filter to just the features for this item
            layer.setSubsetString(f'{id_field} = {id_value}')

            # Set a parent assessment variable
            QgsExpressionContextUtils.setLayerVariable(layer, id_field, id_value)
            # Set the default value from the variable
            field_index = layer.fields().indexFromName(id_field)
            layer.setDefaultValueDefinition(field_index, QgsDefaultValue(f'@{id_field}'))

        # Finally add the new layer here
        QgsProject.instance().addMapLayer(layer, False)
        tree_layer_node = parent_group.addLayer(layer)
        tree_layer_node.setCustomProperty(self.product_key, self.__get_custom_property(project_key, db_item))

        if zoom:
            iface.setActiveLayer(layer)
            iface.zoomToActiveLayer()

        return layer

    def create_machine_code_feature_layer(self, project_key: str, parent_group: QgsLayerTreeGroup, fc_path: str, machine_code: str, display_label: str, symbology_key: str = None, driver: str = 'ogr') -> QgsVectorLayer:
        """
        Creates a new feature layer for the specified machine code and adds it to the map.
        args:
            project_key: The project key
                db_item: The DBItem to create a layer for
                symbology: The symbology to apply to the layer. File name only. No folder or extension."""

        zoom = self.test_for_zoom()

        layer = self.get_machine_code_layer(project_key, machine_code, None)
        if layer is not None:
            return layer

        # Create a layer from the table
        layer = QgsVectorLayer(fc_path, display_label, driver)
        QgsProject.instance().addMapLayer(layer, False)

        # Apply symbology
        if symbology_key is not None:
            symbology_filename = symbology_key if symbology_key.endswith('.qml') else f'{symbology_key}.qml'
            qml = os.path.join(self.symbology_folder, symbology_filename)
            layer.loadNamedStyle(qml)

        # Finally add the new layer here
        tree_layer_node = parent_group.addLayer(layer)
        tree_layer_node.setCustomProperty(self.product_key, self.__get_machine_code_custom_property(project_key, machine_code))

        if zoom:
            iface.setActiveLayer(layer)
            iface.zoomToActiveLayer()

        return layer

    def create_temporary_feature_layer(self, project_key: str, fc_path: str, machine_code: str, display_label: str, symbology_key: str = None, driver: str = 'ogr', private_layer=True) -> QgsVectorLayer:
        """
        Creates a new feature layer for the specified machine code and adds it to the top of the map.
        args:
            project_key: The project key
                db_item: The DBItem to create a layer for
                symbology: The symbology to apply to the layer. File name only. No folder or extension."""

        layer = self.get_machine_code_layer(project_key, machine_code, None)
        if layer is not None:
            return layer

        parent_group = QgsProject.instance().layerTreeRoot()

        # Create a layer from the table
        layer = QgsVectorLayer(fc_path, display_label, driver)
        QgsProject.instance().addMapLayer(layer, False)
        if private_layer:
            layer.setFlags(QgsMapLayer.LayerFlag(QgsMapLayer.Private + QgsMapLayer.Removable))

        # Apply symbology
        if symbology_key is not None:
            symbology_filename = symbology_key if symbology_key.endswith('.qml') else f'{symbology_key}.qml'
            qml = os.path.join(self.symbology_folder, symbology_filename)
            layer.loadNamedStyle(qml)

        # Finally add the new layer here
        tree_layer_node = parent_group.insertLayer(0, layer)
        tree_layer_node.setCustomProperty(self.product_key, self.__get_machine_code_custom_property(project_key, machine_code))

        return layer

    def create_db_item_raster_layer(self, project_key: str, parent_group: QgsLayerTreeGroup, raster_path: str, raster: DBItem, symbology_key: str = None):

        zoom = self.test_for_zoom()

        raster_layer = QgsRasterLayer(raster_path, raster.name)
        QgsProject.instance().addMapLayer(raster_layer, False)
        if symbology_key is not None:
            symbology_filename = symbology_key if symbology_key.endswith('.qml') else f'{symbology_key}.qml'
            qml = os.path.join(self.symbology_folder, symbology_filename)
            raster_layer.loadNamedStyle(qml)
        tree_layer_node = parent_group.addLayer(raster_layer)
        tree_layer_node.setCustomProperty(self.product_key, self.__get_custom_property(project_key, raster))

        if zoom:
            iface.setActiveLayer(raster_layer)
            iface.zoomToActiveLayer()

        return raster_layer

    def create_machine_code_raster_layer(self, project_key: str, parent_group: QgsLayerTreeGroup, raster_path: str, raster: DBItem, machine_code, symbology_key: str = None):

        zoom = self.test_for_zoom()

        raster_layer = QgsRasterLayer(raster_path, raster.name)
        QgsProject.instance().addMapLayer(raster_layer, False)
        if symbology_key is not None:
            symbology_filename = symbology_key if symbology_key.endswith('.qml') else f'{symbology_key}.qml'
            qml = os.path.join(self.symbology_folder, symbology_filename)
            raster_layer.loadNamedStyle(qml)
        tree_layer_node = parent_group.addLayer(raster_layer)
        tree_layer_node.setCustomProperty(self.product_key, self.__get_machine_code_custom_property(project_key, machine_code))

        if zoom:
            iface.setActiveLayer(raster_layer)
            iface.zoomToActiveLayer()

        return raster_layer

    def create_basemap_raster_layer(self, basemap_name: str, basemap_path: str, provider: str):

        basemap_group = self.get_group_layer('Basemaps', 'Basemaps', 'Riverscapes Basemaps', add_missing=True, add_to_bottom=True)
        raster_layer = QgsRasterLayer(basemap_path, basemap_name, provider)
        QgsProject.instance().addMapLayer(raster_layer, False)

        tree_layer_node = basemap_group.addLayer(raster_layer)
        tree_layer_node.setCustomProperty(self.product_key, self.__get_machine_code_custom_property('Basemaps', basemap_name))

        return raster_layer

    def apply_raster_single_value(self, raster_layer: QgsRasterLayer, raster_value: float, max, inverse=False) -> None:

        fcn = QgsColorRampShader()
        fcn.setColorRampType(QgsColorRampShader.Discrete)
        if inverse is True:
            fcn.setColorRampItemList([QgsColorRampShader.ColorRampItem(raster_value, QColor(0, 0, 255, 0), ''),  # QColorConstants.Transparent
                                      QgsColorRampShader.ColorRampItem(max, QColor(255, 20, 225, 200), f'Threshold {raster_value}')])
        else:
            fcn.setColorRampItemList([QgsColorRampShader.ColorRampItem(raster_value, QColor(255, 20, 225, 200), f'Threshold {raster_value}')])
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fcn)

        renderer = QgsSingleBandPseudoColorRenderer(raster_layer.dataProvider(), 1, shader)
        raster_layer.setRenderer(renderer)
        raster_layer.triggerRepaint()

    # Set Fields
    def set_multiline(self, feature_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        widget_setup = QgsEditorWidgetSetup('TextEdit', {'IsMultiline': True, 'UseHtml': False})
        feature_layer.setEditorWidgetSetup(field_index, widget_setup)
        feature_layer.setFieldAlias(field_index, field_alias)
        form_config = feature_layer.editFormConfig()
        form_config.setLabelOnTop(field_index, True)
        feature_layer.setEditFormConfig(form_config)

    def set_hidden(self, feature_layer: QgsVectorLayer, field_name: str, field_alias: str) -> None:
        """Sets a field to hidden, read only, and also sets an alias just in case. Often used on fid, project_id, and event_id"""
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        form_config = feature_layer.editFormConfig()
        form_config.setReadOnly(field_index, True)
        feature_layer.setEditFormConfig(form_config)
        feature_layer.setFieldAlias(field_index, field_alias)
        widget_setup = QgsEditorWidgetSetup('Hidden', {})
        feature_layer.setEditorWidgetSetup(field_index, widget_setup)

    def set_alias(self, feature_layer: QgsVectorLayer, field_name: str, field_alias: str, parent_container=None, display_index=None) -> None:
        """Just provides an alias to the field for display"""
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        feature_layer.setFieldAlias(field_index, field_alias)
        if parent_container is not None and display_index is not None:
            form_config = feature_layer.editFormConfig()
            editor_field = QgsAttributeEditorField(field_name, display_index, parent_container)
            parent_container.addChildElement(editor_field)
            feature_layer.setEditFormConfig(form_config)

    def set_table_as_layer_variable(self, feature_layer: QgsVectorLayer, database: str, table: str):
        conn = sqlite3.connect(database)
        curs = conn.cursor()
        curs.execute("SELECT * FROM {};".format(table))
        lookup_collection = curs.fetchall()
        conn.commit()
        conn.close()
        QgsExpressionContextUtils.setLayerVariable(feature_layer, table, json.dumps(lookup_collection))

    def set_value_map(self, feature_layer: QgsVectorLayer, field_name: str, database: str, lookup_table_name: str, field_alias: str, parent_container=None, display_index=None, expression=None) -> None:

        desc_position = 1
        value_position = 0
        reuse_last = True
        """Will set a Value Map widget drop down list from the lookup database table"""
        conn = sqlite3.connect(database)
        curs = conn.cursor()
        curs.execute("SELECT * FROM {};".format(lookup_table_name))
        lookup_collection = curs.fetchall()
        conn.commit()
        conn.close()
        # make a dictionary from the returned values
        lookup_list = []
        for row in lookup_collection:
            key = str(row[desc_position])
            value = row[value_position]
            lookup_list.append({key: value})
        lookup_config = {
            'map': lookup_list
        }
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        if expression is not None:
            # Set field to display vegetation dam density based on values in other fields
            virtual_field = QgsField(field_name, QVariant.Int)
            feature_layer.addExpressionField(expression, virtual_field)
            feature_layer.setDefaultValueDefinition(field_index, QgsDefaultValue(expression))
        widget_setup = QgsEditorWidgetSetup('ValueMap', lookup_config)
        feature_layer.setEditorWidgetSetup(field_index, widget_setup)
        feature_layer.setFieldAlias(field_index, field_alias)
        form_config = feature_layer.editFormConfig()
        form_config.setReuseLastValue(field_index, reuse_last)
        if parent_container is not None and display_index is not None:
            editor_field = QgsAttributeEditorField(field_name, display_index, parent_container)
            parent_container.addChildElement(editor_field)
        feature_layer.setEditFormConfig(form_config)

    # ----- LAYER ACTION BUTTONS -----------
    def add_help_action(self, feature_layer: QgsVectorLayer, help_slug: str, parent_container: QgsAttributeEditorContainer):

        help_action_text = dedent("""
                           import webbrowser
                           help_url = "[% @help_url %]"
                           webbrowser.open(help_url, new=2)
                           """).strip("\n")
        help_url = CONSTANTS['webUrl'].rstrip('/') + '/Software_Help/' + help_slug.strip('/') + '.html' if help_slug is not None and len(help_slug) > 0 else CONSTANTS
        QgsExpressionContextUtils.setLayerVariable(feature_layer, 'help_url', help_url)
        helpAction = QgsAction(1, 'Open Help URL', help_action_text, None, capture=False, shortTitle='Help', actionScopes={'Layer'})
        feature_layer.actions().addAction(helpAction)
        editorAction = QgsAttributeEditorAction(helpAction, parent_container)
        parent_container.addChildElement(editorAction)

    # ----- CREATING VIRTUAL FIELDS --------

    def set_virtual_dimension(self, feature_layer: QgsVectorLayer, dimension: str) -> None:
        """dimension should be 'area' or 'length'
        sets a virtual length field named vrt_length
        aliases the field as Length (m)
        sets the widget type to text
        sets default value to the dimension expression"""

        field_name = 'vrt_' + dimension
        field_alias = dimension.capitalize() + ' (m)'
        field_expression = 'round(${}, 0)'.format(dimension)
        virtual_field = QgsField(field_name, QVariant.Int)
        feature_layer.addExpressionField(field_expression, virtual_field)
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        feature_layer.setFieldAlias(field_index, field_alias)
        feature_layer.setDefaultValueDefinition(field_index, QgsDefaultValue(field_expression))
        widget_setup = QgsEditorWidgetSetup('TextEdit', {})
        feature_layer.setEditorWidgetSetup(field_index, widget_setup)

    def set_created_datetime(self, feature_layer: QgsVectorLayer) -> None:
        """Will set a date time created field to a default value of now() and also set it to read only"""

        fields = feature_layer.fields()
        field_index = fields.indexFromName('created')
        feature_layer.setFieldAlias(field_index, 'Created')
        feature_layer.setDefaultValueDefinition(field_index, QgsDefaultValue("now()"))
        form_config = feature_layer.editFormConfig()
        form_config.setReadOnly(field_index, True)
        feature_layer.setEditFormConfig(form_config)

    def set_label(self, feature_layer: QgsVectorLayer, label_field: str) -> None:
        """Sets the label field for the layer
        Labeling learned here:
        https://gis.stackexchange.com/questions/273266/reading-and-setting-label-settings-in-pyqgis/273268#273268
        """
        layer_settings = QgsPalLayerSettings()
        layer_settings.fieldName = label_field
        layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
        feature_layer.setLabelsEnabled(True)
        feature_layer.setLabeling(layer_settings)

    def set_field_constraint_not_null(self, feature_layer: QgsVectorLayer, field_name: str, constraint_strength: int) -> None:
        """Sets a not null constraint and strength"""
        if constraint_strength == 1:
            strength = QgsFieldConstraints.ConstraintStrengthSoft
        elif constraint_strength == 2:
            strength = QgsFieldConstraints.ConstraintStrengthHard
        fields = feature_layer.fields()
        field_index = fields.indexFromName(field_name)
        feature_layer.setFieldConstraint(field_index, QgsFieldConstraints.ConstraintNotNull, strength)
