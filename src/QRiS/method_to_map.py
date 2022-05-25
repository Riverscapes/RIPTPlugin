from locale import CODESET
import os
import sqlite3

from random import randint, randrange


from PyQt5.QtWidgets import QMessageBox

from qgis.core import (
    QgsField,
    QgsLayerTreeGroup,
    QgsVectorLayer,
    QgsDefaultValue,
    QgsEditorWidgetSetup,
    QgsFeatureRequest,
    QgsSymbol,
    QgsRendererCategory,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsFillSymbol,
    QgsSimpleFillSymbolLayer,
    QgsCategorizedSymbolRenderer,
    QgsProject,
    QgsExpressionContextUtils)

from qgis.PyQt.QtGui import QStandardItem, QColor
from qgis.PyQt.QtCore import Qt, QVariant

from ..model.assessment import ASSESSMENT_MACHINE_CODE

# path to symbology directory
symbology_path = os.path.dirname(os.path.dirname(__file__))


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def add_assessment_method_to_map(qris_project, assessment_method_id: int):
    """Starts with an assessment_method_id and then adds all of the filtered layers for that assessment and method"""
    # First, check if the assessments table has been added as hidden in the project, if not add it
    if len(QgsProject.instance().mapLayersByName('assessments')) == 0:
        assessments_path = qris_project.project_file + '|layername=' + 'assessments'
        assessments_layer = QgsVectorLayer(assessments_path, 'assessments', 'ogr')
        QgsProject.instance().addMapLayer(assessments_layer, False)

    # 2. Queries the method_layers table and gets a list of layers required for that method -done
    # a. also returns the parent assessment_id
    conn = sqlite3.connect(qris_project.project_file)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute("""SELECT projects.name AS project_name,
                    assessments.fid AS assessment_id,
                    assessments.name AS assessment_name,
                    assessment_methods.fid AS assessment_method_id,
                    methods.fid AS method_id,
                    layers.fid AS layer_id,
                    layers.fc_name,
                    layers.display_name,
                    layers.geom_type,
                    layers.is_lookup,
                    layers.qml FROM projects INNER
                    JOIN((methods
                    INNER JOIN (assessments
                    INNER JOIN assessment_methods ON assessments.fid = assessment_methods.assessment_id)
                    ON methods.fid = assessment_methods.method_id)
                    INNER JOIN (layers
                    INNER JOIN method_layers
                    ON layers.fid = method_layers.layer_id)
                    ON methods.fid = method_layers.method_id)
                    WHERE (((assessment_methods.fid)=?));""", [assessment_method_id])
    method_layers = curs.fetchall()
    conn.commit()
    conn.close()

    # Create the layer group list and set the target assessment group
    project_group_name = str(method_layers[0]['project_name'])
    assessment_group_name = str(method_layers[0]['assessment_id']) + '-' + method_layers[0]['assessment_name']
    group_lineage = [project_group_name, ASSESSMENT_MACHINE_CODE, assessment_group_name]
    assessment_group = set_target_layer_group(group_lineage)

    # now loop through each layer and see if they need to be added
    spatial_layers = []
    for layer in method_layers:
        # set the layer path
        layer['path'] = qris_project.project_file + '|layername=' + layer['fc_name']
        layer['ass_name'] = str(layer['assessment_id']) + '-' + layer['display_name']
        # check if it's a lookup layer, if it is send it on
        if layer['is_lookup']:
            add_lookup_table(layer)
        else:
            # add layer to spatial layers list, ensures that all lookups are added to the project first
            spatial_layers.append(layer)

    # now deal with the spatial layers
    for layer in spatial_layers:
        # check if the layer has already been added.
        if len(QgsProject.instance().mapLayersByName(layer['ass_name'])) == 0:
            # if not make a layer out of it
            map_layer = QgsVectorLayer(layer['path'], layer['fc_name'], 'ogr')
            QgsProject.instance().addMapLayer(map_layer, False)
            map_layer.setName(layer['ass_name'])
            # Set the QML symbology
            qml = os.path.join(symbology_path, 'symbology', layer['qml'])
            map_layer.loadNamedStyle(qml)
            # Set the assessment definition query
            map_layer.setSubsetString('assessment_id = ' + str(layer['assessment_id']))
            # Set a parent assessment variable
            QgsExpressionContextUtils.setLayerVariable(map_layer, 'assessment_id', layer['assessment_id'])
            # Set the default value from the variable
            assessment_field_index = map_layer.fields().indexFromName('assessment_id')
            map_layer.setDefaultValueDefinition(assessment_field_index, QgsDefaultValue("@assessment_id"))
            # finally add the layer to the group
            assessment_group.addLayer(map_layer)
            # send to layer specific add to map functions
            fc_name = layer['fc_name']
            if fc_name == 'dam_crests':
                add_dam_crests(map_layer)
            elif fc_name == 'thalwegs':
                add_thalwegs(map_layer)
            elif fc_name == 'inundation_extents':
                add_inundation_extents(map_layer)
            elif fc_name == 'dams':
                add_dams(map_layer)
            elif fc_name == 'jams':
                add_jams(map_layer)
            else:
                pass


# ---------- GROUP STUFF -----------


def set_target_layer_group(group_list: list) -> QgsLayerTreeGroup:
    """
    Looks for each item in the group_list recursively adding missing children as needed.
    group_list should consist of needed strings for text matching at each level of the tree heierarchy.
    returns the target group at which layers should be added.
    """
    # get the layer tree root and set to group to start
    # TODO: consider adding cusome properties to groups using for identification in the tree.
    # from ..model.assessment import ASSESSMENT_MACHINE_CODE
    # 'qris_type': ASSESSMENT_MACHINE_CODE
    # 'qris_id': fid
    group = QgsProject.instance().layerTreeRoot()
    # set the list of group names to search
    for group_name in group_list:
        if not any([child.name() == group_name for child in group.children()]):
            # if it ain't there add it is a new group and set to group for recursion
            new_group = group.addGroup(group_name)
            group = new_group
        else:
            # if it is there set it as the next group to search
            group = next(child for child in group.children() if child.name() == group_name)
    return group


# -------- LAYER SPECIFIC ADD TO MAP FUNCTIONS ---------
def add_lookup_table(layer: dict):
    """Checks if a lookup table has been added as private in the current QGIS session"""
    # Check if the lookup table has been added
    # TODO make sure the lookup tables are actually from the correct project geopackage
    # TODO Use custom properties to double check that the correct layers are being used
    if len(QgsProject.instance().mapLayersByName(layer['fc_name'])) == 0:
        lookup_layer = QgsVectorLayer(layer['path'], layer['fc_name'], 'ogr')
        # TODO consider adding and then marking as private instead of using the False flag
        QgsProject.instance().addMapLayer(lookup_layer, False)


def add_dam_crests(map_layer: QgsVectorLayer):
    set_hidden(map_layer, 'fid', 'Dam Crests ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'structure_source_id', 'lkp_structure_source', 'Structure Source')
    set_value_relation(map_layer, 'dam_integrity_id', 'lkp_dam_integrity', 'Dam Integrity')
    set_value_relation(map_layer, 'beaver_maintenance_id', 'lkp_beaver_maintenance', 'Beaver Maintenance')
    set_alias(map_layer, 'height', 'Dam Height')
    set_virtual_dimension(map_layer, 'length')


def add_dams(map_layer: QgsVectorLayer):
    set_hidden(map_layer, 'fid', 'Dam ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'structure_source_id', 'lkp_structure_source', 'Structure Source')
    set_value_relation(map_layer, 'dam_integrity_id', 'lkp_dam_integrity', 'Dam Integrity')
    set_value_relation(map_layer, 'beaver_maintenance_id', 'lkp_beaver_maintenance', 'Beaver Maintenance')
    set_alias(map_layer, 'length', 'Dam Length')
    set_alias(map_layer, 'height', 'Dam Height')


def add_jams(map_layer: QgsVectorLayer):
    set_hidden(map_layer, 'fid', 'Jam ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'structure_source_id', 'lkp_structure_source', 'Structure Source')
    set_value_relation(map_layer, 'beaver_maintenance_id', 'lkp_beaver_maintenance', 'Beaver Maintenance')
    set_alias(map_layer, 'wood_count', 'Wood Count')
    set_alias(map_layer, 'length', 'Jam Length')
    set_alias(map_layer, 'width', 'Jam Width')
    set_alias(map_layer, 'height', 'Jam Height')


def add_inundation_extents(map_layer: QgsVectorLayer):
    set_hidden(map_layer, 'fid', 'Extent ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'type_id', 'lkp_inundation_extent_types', 'Extent Type')
    set_virtual_dimension(map_layer, 'area')


def add_thalwegs(map_layer: QgsVectorLayer):
    set_hidden(map_layer, 'fid', 'Thalweg ID')
    set_hidden(map_layer, 'assessment_id', 'Assessment ID')
    set_value_relation(map_layer, 'type_id', 'lkp_thalweg_types', 'Thalweg Type')
    set_virtual_dimension(map_layer, 'length')


# ------ SETTING FIELD AND FORM PROPERTIES -------
def set_value_relation(map_layer: QgsVectorLayer, field_name: str, lookup_table_name: str, field_alias: str, reuse_last: bool = True):
    """Adds a Value Relation widget to the QGIS entry form. Note that at this time it assumes a Key of fid and value of name"""
    # value relation widget configuration. Just add the Layer name
    lookup_config = {
        'AllowMulti': False,
        'AllowNull': False,
        'Key': 'fid',
        'Layer': '',
        'NofColumns': 1,
        'OrderByValue': False,
        'UseCompleter': False,
        'Value': 'name'
    }
    lookup_layer_id = QgsProject.instance().mapLayersByName(lookup_table_name)[0].id()
    lookup_config['Layer'] = lookup_layer_id
    fields = map_layer.fields()
    field_index = fields.indexFromName(field_name)
    widget_setup = QgsEditorWidgetSetup('ValueRelation', lookup_config)
    map_layer.setEditorWidgetSetup(field_index, widget_setup)
    map_layer.setFieldAlias(field_index, field_alias)
    form_config = map_layer.editFormConfig()
    form_config.setReuseLastValue(field_index, reuse_last)
    map_layer.setEditFormConfig(form_config)


def set_hidden(map_layer: QgsVectorLayer, field_name: str, field_alias: str):
    """Sets a field to hidden, read only, and also sets an alias just in case. Often used on fid, project_id, and assessment_id"""
    fields = map_layer.fields()
    field_index = fields.indexFromName(field_name)
    form_config = map_layer.editFormConfig()
    form_config.setReadOnly(field_index, True)
    map_layer.setEditFormConfig(form_config)
    map_layer.setFieldAlias(field_index, field_alias)
    widget_setup = QgsEditorWidgetSetup('Hidden', {})
    map_layer.setEditorWidgetSetup(field_index, widget_setup)


def set_alias(map_layer: QgsVectorLayer, field_name: str, field_alias: str):
    """Just provides an alias to the field for display"""
    fields = map_layer.fields()
    field_index = fields.indexFromName(field_name)
    map_layer.setFieldAlias(field_index, field_alias)


# ----- CREATING VIRTUAL FIELDS --------
def set_virtual_dimension(map_layer: QgsVectorLayer, dimension: str):
    """dimension should be 'area' or 'length'
    sets a virtual length field named vrt_length
    aliases the field as Length
    sets the widget type to text
    sets default value to the length expression"""
    field_name = 'vrt_' + dimension
    field_alias = dimension.capitalize()
    field_expression = 'round(${}, 0)'.format(dimension)
    virtual_field = QgsField(field_name, QVariant.Int)
    map_layer.addExpressionField(field_expression, virtual_field)
    fields = map_layer.fields()
    field_index = fields.indexFromName(field_name)
    map_layer.setFieldAlias(field_index, field_alias)
    map_layer.setDefaultValueDefinition(field_index, QgsDefaultValue(field_expression))
    widget_setup = QgsEditorWidgetSetup('TextEdit', {})
    map_layer.setEditorWidgetSetup(field_index, widget_setup)
