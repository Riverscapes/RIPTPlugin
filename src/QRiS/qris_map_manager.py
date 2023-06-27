import os
import sqlite3
from textwrap import dedent

from .riverscapes_map_manager import RiverscapesMapManager

from ..model.project import Project, PROJECT_MACHINE_CODE
from ..model.mask import Mask, MASK_MACHINE_CODE, AOI_MACHINE_CODE, AOI_MASK_TYPE_ID
from ..model.stream_gage import StreamGage, STREAM_GAGE_MACHINE_CODE
from ..model.scratch_vector import ScratchVector, SCRATCH_VECTOR_MACHINE_CODE
from ..model.pour_point import PourPoint
from ..model.raster import Raster, BASEMAP_MACHINE_CODE, SURFACE_MACHINE_CODE, CONTEXT_MACHINE_CODE, RASTER_SLIDER_MACHINE_CODE, get_raster_symbology
from ..model.event import EVENT_MACHINE_CODE, DESIGN_EVENT_TYPE_ID, DESIGN_MACHINE_CODE, Event
from ..model.event_layer import EventLayer
from ..model.profile import Profile
from ..model.cross_sections import CrossSections

from .path_utilities import parse_posix_path

from qgis.core import (
    QgsVectorLayer,
    QgsMapLayer,
    QgsProject,
    QgsExpressionContextUtils,
    qgsfunction,
    QgsAttributeEditorContainer,
    QgsAction,
    QgsAttributeEditorAction
)


class QRisMapManager(RiverscapesMapManager):

    def __init__(self, project: Project) -> None:
        super().__init__('QRiS')
        self.project = project
        self.layer_order = [
            CrossSections.CROSS_SECTIONS_MACHINE_CODE,
            Profile.PROFILE_MACHINE_CODE,
            AOI_MACHINE_CODE,
            MASK_MACHINE_CODE,
            f'{EVENT_MACHINE_CODE}_ROOT',
            f'{DESIGN_MACHINE_CODE}_ROOT',
            STREAM_GAGE_MACHINE_CODE,
            f'{RASTER_SLIDER_MACHINE_CODE}_ROOT',
            CONTEXT_MACHINE_CODE,
            SURFACE_MACHINE_CODE,
            'QRiS Base Maps',
            BASEMAP_MACHINE_CODE]

    def build_mask_layer(self, mask: Mask) -> QgsMapLayer:

        if mask.mask_type.id == AOI_MASK_TYPE_ID:
            group_layer_name = 'AOIs'
            mask_machine_code = AOI_MACHINE_CODE
            symbology = 'mask'  # TODO do aois need a different mask type? make the reference here...
            layer_name = 'aoi_features'
        else:
            group_layer_name = 'Sampling Frames'
            mask_machine_code = MASK_MACHINE_CODE
            symbology = 'sampling_frames'
            layer_name = 'mask_features'

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, mask_machine_code, group_layer_name, project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, mask, group_layer)
        if existing_layer is not None:
            return existing_layer

        fc_path = f'{self.project.project_file}|layername={layer_name}'
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, mask, 'mask_id', symbology)

        # setup fields
        self.set_hidden(feature_layer, 'fid', 'Mask Feature ID')
        self.set_hidden(feature_layer, 'mask_id', 'Mask ID')
        self.set_alias(feature_layer, 'position', 'Position')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_hidden(feature_layer, 'metadata', 'Metadata')
        self.set_virtual_dimension(feature_layer, 'area')

        if not mask.mask_type.id == AOI_MASK_TYPE_ID:
            feature_layer.setLabelsEnabled(True)
            feature_layer.setCustomProperty("labeling/fieldName", 'display_label')

        return feature_layer

    def build_profile_layer(self, profile: Profile) -> QgsMapLayer:

        if profile.profile_type_id == Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE:
            symbology = 'centerline'
            layer_name = 'profile_centerlines'
        else:
            symbology = 'profile'
            layer_name = 'profile_features'

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, Profile.PROFILE_MACHINE_CODE, 'Profiles', project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, profile, group_layer)
        if existing_layer is not None:
            return existing_layer

        fc_path = f'{self.project.project_file}|layername={layer_name}'
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, profile, 'profile_id', symbology)

        # setup fields
        self.set_hidden(feature_layer, 'fid', 'Profile Feature ID')
        self.set_hidden(feature_layer, 'profile_id', 'Profile ID')
        self.set_alias(feature_layer, 'position', 'Position')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_hidden(feature_layer, 'metadata', 'Metadata')
        self.set_virtual_dimension(feature_layer, 'length')

        return feature_layer

    def build_cross_section_layer(self, cross_sections: CrossSections) -> QgsMapLayer:

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, CrossSections.CROSS_SECTIONS_MACHINE_CODE, 'Cross Sections', project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, cross_sections, group_layer)
        if existing_layer is not None:
            return existing_layer

        fc_path = f'{self.project.project_file}|layername=cross_section_features'
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, cross_sections, 'cross_section_id', 'cross_sections')

        # setup fields
        self.set_hidden(feature_layer, 'fid', 'Cross Section Feature ID')
        self.set_hidden(feature_layer, 'cross_section_id', 'Cross Sections ID')
        self.set_alias(feature_layer, 'position', 'Position')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_hidden(feature_layer, 'metadata', 'Metadata')
        self.set_virtual_dimension(feature_layer, 'length')

        return feature_layer

    def build_stream_gage_layer(self) -> QgsMapLayer:

        existing_layer = self.get_machine_code_layer(self.project.map_guid, STREAM_GAGE_MACHINE_CODE, None)
        if existing_layer is not None:
            return existing_layer

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        # TODO Do stream guages need a Group layer?
        fc_path = self.project.project_file + '|layername=' + 'stream_gages'
        feature_layer = self.create_machine_code_feature_layer(self.project.map_guid, project_group, fc_path, STREAM_GAGE_MACHINE_CODE, 'Stream Gages', 'stream_gages')

        # Apply labels
        self.set_label(feature_layer, 'site_code')

        return feature_layer

    def build_scratch_vector(self, vector: ScratchVector):

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, CONTEXT_MACHINE_CODE, 'Context', project_group, True)
        fc_path: str = vector.gpkg_path + '|layername=' + vector.fc_name
        existing_layer = self.get_db_item_layer(self.project.map_guid, vector, None)
        if existing_layer is not None:
            return
        layer = self.create_db_item_feature_layer(self.project.map_guid, group_layer, fc_path, vector, None, 'vector')

        return layer

    def build_pour_point_map_layer(self, pour_point: PourPoint):

        existing_layer = self.get_db_item_layer(self.project.map_guid, pour_point, None)
        if existing_layer is not None:
            return

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        context_group_layer = self.get_group_layer(self.project.map_guid, CONTEXT_MACHINE_CODE, 'Context', project_group, True)
        pour_point_group_layer = self.get_group_layer(self.project.map_guid, pour_point, pour_point.name, context_group_layer, True)  # TODO check here

        # Create a layer from the pour point
        point_fc_path = self.project.project_file + '|layername=' + 'pour_points'
        # point_feature_layer = self.create_db_item_feature_layer(self.project.map_guid, pour_point_group_layer, point_fc_path, pour_point, 'fid', 'pour_point')
        point_feature_layer = QgsVectorLayer(point_fc_path, 'Pour Point', 'ogr')
        point_feature_layer.setSubsetString('fid = ' + str(pour_point.id))
        QgsProject.instance().addMapLayer(point_feature_layer, False)
        pour_point_group_layer.addLayer(point_feature_layer)
        qml = parse_posix_path(os.path.join(self.symbology_folder, 'pour_point.qml'))
        point_feature_layer.loadNamedStyle(qml)

        catchment_fc_path = self.project.project_file + '|layername=' + 'catchments'
        # catchment_feature_layer = self.create_db_item_feature_layer(self.project.map_guid, pour_point_group_layer, catchment_fc_path, pour_point, 'fid', 'catchment')
        catchment_feature_layer = QgsVectorLayer(catchment_fc_path, 'Catchment', 'ogr')
        catchment_feature_layer.setSubsetString('pour_point_id = ' + str(pour_point.id))
        QgsExpressionContextUtils.setLayerVariable(catchment_feature_layer, 'pour_point_id', pour_point.id)
        qml = parse_posix_path(os.path.join(self.symbology_folder, 'catchment.qml'))
        catchment_feature_layer.loadNamedStyle(qml)
        QgsProject.instance().addMapLayer(catchment_feature_layer, False)
        pour_point_group_layer.addLayer(catchment_feature_layer)

        return point_feature_layer, catchment_feature_layer

    def build_raster_layer(self, raster: Raster) -> QgsMapLayer:

        if raster.is_context is False:
            raster_machine_code = SURFACE_MACHINE_CODE
            group_layer_name = 'Surfaces'
        else:
            raster_machine_code = CONTEXT_MACHINE_CODE
            group_layer_name = 'Context'
        # else:
        #     raster_machine_code = BASEMAP_MACHINE_CODE
        #     group_layer_name = 'Basemaps'

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, raster_machine_code, group_layer_name, project_group, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, raster, None)  # TODO search entire toc or just project??
        if existing_layer is not None:
            return existing_layer

        raster_path = parse_posix_path(os.path.join(os.path.dirname(self.project.project_file), raster.path))
        symbology = None
        symbology_key = get_raster_symbology(self.project.project_file, raster.raster_type_id)
        if symbology_key is not None:
            symbology = parse_posix_path(os.path.join(os.path.dirname(self.symbology_folder), symbology_key))
        raster_layer = self.create_db_item_raster_layer(self.project.map_guid, group_layer, raster_path, raster, symbology)

        return raster_layer

    def build_raster_slider_layer(self, raster: Raster) -> QgsMapLayer:

        # Add raster normally as a contextual layer
        self.build_raster_layer(raster)

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        group_layer = self.get_group_layer(self.project.map_guid, f'{RASTER_SLIDER_MACHINE_CODE}_ROOT', 'Raster Slider', project_group, True)

        # Remove any existing raster layer in this group
        group_layer.removeAllChildren()

        raster_path = parse_posix_path(os.path.join(os.path.dirname(self.project.project_file), raster.path))
        raster_layer = self.create_machine_code_raster_layer(self.project.map_guid, group_layer, raster_path, raster, RASTER_SLIDER_MACHINE_CODE)

        return raster_layer

    def build_event_single_layer(self, event: Event, event_layer: EventLayer) -> None:
        """
        Add a single layer for an event
        """
        # if lookup table then forget about it
        if event_layer.layer.is_lookup:
            return

        machine_code = DESIGN_MACHINE_CODE if event.event_type.id == DESIGN_EVENT_TYPE_ID else EVENT_MACHINE_CODE
        group_name = 'Designs' if event.event_type.id == DESIGN_EVENT_TYPE_ID else 'Data Capture Events'

        project_group = self.get_group_layer(self.project.map_guid, PROJECT_MACHINE_CODE, self.project.name, None, True)
        events_group_layer = self.get_group_layer(self.project.map_guid, f'{machine_code}_ROOT', group_name, project_group, True)
        event_group_layer = self.get_group_layer(self.project.map_guid, f'{machine_code}_{event.id}', event.name, events_group_layer, True)

        existing_layer = self.get_db_item_layer(self.project.map_guid, event_layer, event_group_layer)
        if existing_layer is not None:
            return

        fc_path = self.project.project_file + '|layername=' + event_layer.layer.fc_name
        feature_layer = self.create_db_item_feature_layer(self.project.map_guid, event_group_layer, fc_path, event_layer, 'event_id', event_layer.layer.qml)

        # send to layer specific field handlers
        layer_name = event_layer.layer.fc_name
        if layer_name == 'dam_crests':
            self.configure_dam_crests(feature_layer)
        elif layer_name == 'thalwegs':
            self.configure_thalwegs(feature_layer)
        elif layer_name == 'inundation_extents':
            self.configure_inundation_extents(feature_layer)
        elif layer_name == 'dams':
            self.configure_dams(feature_layer)
        elif layer_name == 'jams':
            self.configure_jams(feature_layer)
        elif layer_name == 'channel_unit_points':
            self.configure_channel_unit_points(feature_layer)
        elif layer_name == 'channel_unit_polygons':
            self.configure_channel_unit_polygons(feature_layer)
        elif layer_name == 'active_extents':
            self.configure_active_extents(feature_layer)
        elif layer_name == 'zoi':
            self.configure_zoi(feature_layer)
        elif layer_name == 'structure_points':
            self.configure_structure_points(feature_layer)
        elif layer_name == 'structure_lines':
            self.configure_structure_lines(feature_layer)
        elif layer_name == 'complexes':
            self.configure_complexes(feature_layer)
        elif layer_name in ['brat_cis', 'brat_cis_reaches']:
            self.add_brat_cis(feature_layer)
            if layer_name == 'brat_cis_reaches':
                self.create_machine_code_feature_layer(self.project.map_guid, event_group_layer, fc_path, f'{event_layer.event_id}_BRAT_REACHES_SQL', 'SQLBRAT Reaches', 'brat_sql_reaches.qml')
        else:
            # TODO: Should probably have a notification for layers not found....
            pass

    def add_brat_cis(self, feature_layer: QgsVectorLayer) -> None:
        # first read and set the lookup tables
        self.set_table_as_layer_variable(feature_layer, self.project.project_file, "lkp_brat_vegetation_cis")
        self.set_table_as_layer_variable(feature_layer, self.project.project_file, "lkp_brat_combined_cis")

        # attribute form containers: https://gis.stackexchange.com/questions/310287/qgis-editform-layout-settings-in-python
        editFormConfig = feature_layer.editFormConfig()
        editFormConfig.setLayout(1)
        rootContainer = editFormConfig.invisibleRootContainer()
        rootContainer.clear()

        # FID and Event ID will not show up on the form since we cleared them from the root container, but need to set alias for attribute table.
        self.set_hidden(feature_layer, 'fid', 'Brat Cis ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')

        # Info Group Box
        info_container = QgsAttributeEditorContainer('BRAT Observation Event', rootContainer)
        self.set_alias(feature_layer, 'reach_id', 'Reach ID', info_container, 0)
        self.set_alias(feature_layer, 'observation_date', 'Observation Date', info_container, 1)
        self.set_alias(feature_layer, 'reach_length', 'Reach Length (m)', info_container, 2)
        self.set_alias(feature_layer, 'notes', 'Notes', info_container, 3)
        self.set_alias(feature_layer, 'observer_name', 'Observer Name', info_container, 4)
        editFormConfig.addTab(info_container)

        # Add buffer button
        self.add_buffer_action(feature_layer, rootContainer)

        # Vegetation Evidence Group Box
        veg_container = QgsAttributeEditorContainer('Vegetation Evidence CIS', rootContainer)
        self.set_value_map(feature_layer, 'streamside_veg_id', self.project.project_file, 'lkp_brat_vegetation_types', 'Streamside Vegetation', parent_container=veg_container, display_index=0)
        self.set_value_map(feature_layer, 'riparian_veg_id', self.project.project_file, 'lkp_brat_vegetation_types', 'Riparian Vegetation', parent_container=veg_container, display_index=1)
        veg_expression = get_veg_expression(self.project.project_file, 'lkp_brat_vegetation_cis')
        self.set_value_map(feature_layer, 'veg_density_id', self.project.project_file, 'lkp_brat_dam_density', 'Vegetation Dam Density', expression=veg_expression, parent_container=veg_container, display_index=2)
        editFormConfig.addTab(veg_container)

        # Combined Evidence Group Box
        comb_container = QgsAttributeEditorContainer('Combined Evidence CIS', rootContainer)
        self.set_value_map(feature_layer, 'base_streampower_id', self.project.project_file, 'lkp_brat_base_streampower', 'Base Streampower', parent_container=comb_container, display_index=0)
        self.set_value_map(feature_layer, 'high_streampower_id', self.project.project_file, 'lkp_brat_high_streampower', 'High Streampower', parent_container=comb_container, display_index=1)
        self.set_value_map(feature_layer, 'slope_id', self.project.project_file, 'lkp_brat_slope', 'Slope', parent_container=comb_container, display_index=2)
        comb_expression = get_comb_expression(self.project.project_file, 'lkp_brat_combined_cis')
        self.set_value_map(feature_layer, 'combined_density_id', self.project.project_file, 'lkp_brat_dam_density', 'Combined Dam Density', expression=comb_expression, parent_container=comb_container, display_index=3)
        editFormConfig.addTab(comb_container)

        # Add Help Button to Form
        self.add_help_action(feature_layer, 'brat_cis', rootContainer)

        feature_layer.setEditFormConfig(editFormConfig)

        feature_layer.editingStarted.connect(self.stop_brat_edit)
        feature_layer.editingStopped.connect(self.stop_brat_edit)

    def configure_dam_crests(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'Dam Crests ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_value_map(feature_layer, 'structure_source_id', self.project.project_file, 'lkp_structure_source', 'Structure Source')
        self.set_value_map(feature_layer, 'dam_integrity_id', self.project.project_file, 'lkp_dam_integrity', 'Dam Integrity')
        self.set_value_map(feature_layer, 'beaver_maintenance_id', self.project.project_file, 'lkp_beaver_maintenance', 'Beaver Maintenance')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_virtual_dimension(feature_layer, 'length')

    def configure_dams(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'Dam ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_value_map(feature_layer, 'structure_source_id', self.project.project_file, 'lkp_structure_source', 'Structure Source')
        self.set_value_map(feature_layer, 'dam_integrity_id', self.project.project_file, 'lkp_dam_integrity', 'Dam Integrity')
        self.set_value_map(feature_layer, 'beaver_maintenance_id', self.project.project_file, 'lkp_beaver_maintenance', 'Beaver Maintenance')
        self.set_alias(feature_layer, 'length', 'Dam Length')
        self.set_alias(feature_layer, 'height', 'Dam Height')

    def configure_jams(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'Jam ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_value_map(feature_layer, 'structure_source_id', self.project.project_file, 'lkp_structure_source', 'Structure Source')
        self.set_value_map(feature_layer, 'beaver_maintenance_id', self.project.project_file, 'lkp_beaver_maintenance', 'Beaver Maintenance')
        self.set_alias(feature_layer, 'wood_count', 'Wood Count')
        self.set_alias(feature_layer, 'length', 'Jam Length')
        self.set_alias(feature_layer, 'width', 'Jam Width')
        self.set_alias(feature_layer, 'height', 'Jam Height')
        self.set_multiline(feature_layer, 'description', 'Description')

    def configure_inundation_extents(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'Extent ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_value_map(feature_layer, 'type_id', self.project.project_file, 'lkp_inundation_extent_types', 'Extent Type')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_virtual_dimension(feature_layer, 'area')

    def configure_thalwegs(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'Thalweg ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_value_map(feature_layer, 'type_id', self.project.project_file, 'lkp_thalweg_types', 'Thalweg Type')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_virtual_dimension(feature_layer, 'length')

    def configure_channel_unit_points(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_hidden(feature_layer, 'fid', 'Channel Unit ID')
        self.set_value_map(feature_layer, 'unit_type_id', self.project.project_file, 'lkp_channel_unit_types', 'Unit Type')
        self.set_value_map(feature_layer, 'structure_forced_id', self.project.project_file, 'lkp_structure_forced', 'Structure Forced')
        self.set_value_map(feature_layer, 'primary_channel_id', self.project.project_file, 'lkp_primary_channel', 'Primary Channel')
        self.set_value_map(feature_layer, 'primary_unit_id', self.project.project_file, 'lkp_primary_unit', 'Primary Unit')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_alias(feature_layer, 'length', 'Length')
        self.set_alias(feature_layer, 'width', 'Width')
        self.set_alias(feature_layer, 'depth', 'Depth')
        self.set_alias(feature_layer, 'percent_wetted', 'Percent Wetted')
        self.set_multiline(feature_layer, 'description', 'Description')

    def configure_channel_unit_polygons(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_hidden(feature_layer, 'fid', 'Channel Unit ID')
        self.set_value_map(feature_layer, 'unit_type_id', self.project.project_file, 'lkp_channel_unit_types', 'Unit Type')
        self.set_value_map(feature_layer, 'structure_forced_id', self.project.project_file, 'lkp_structure_forced', 'Structure Forced')
        self.set_value_map(feature_layer, 'primary_channel_id', self.project.project_file, 'lkp_primary_channel', 'Primary Channel')
        self.set_value_map(feature_layer, 'primary_unit_id', self.project.project_file, 'lkp_primary_unit', 'Primary Unit')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_alias(feature_layer, 'percent_wetted', 'Percent Wetted')
        self.set_multiline(feature_layer, 'description', 'Description')

    def configure_active_extents(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'Extent ID')
        # We may consider adding a value map for the event ID,
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_value_map(feature_layer, 'type_id', self.project.project_file, 'lkp_active_extent_types', 'Extent Type')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_virtual_dimension(feature_layer, 'area')

    def configure_zoi(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'ZOI ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_value_map(feature_layer, 'type_id', self.project.project_file, 'zoi_types', 'ZOI Type')
        self.set_value_map(feature_layer, 'stage_id', self.project.project_file, 'lkp_zoi_stage', 'ZOI Stage')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_field_constraint_not_null(feature_layer, 'type_id', 1)
        self.set_field_constraint_not_null(feature_layer, 'stage_id', 1)
        self.set_virtual_dimension(feature_layer, 'area')
        self.set_created_datetime(feature_layer)

    def configure_structure_points(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'Structure ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_value_map(feature_layer, 'structure_type_id', self.project.project_file, 'structure_types', 'Structure Type')
        self.set_alias(feature_layer, 'name', 'Structure Name')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_alias(feature_layer, 'created', 'Created')
        self.set_field_constraint_not_null(feature_layer, 'structure_type_id', 1)
        self.set_created_datetime(feature_layer)

    def configure_structure_lines(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'Structure ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_value_map(feature_layer, 'structure_type_id', self.project.project_file, 'structure_types', 'Structure Type')
        self.set_alias(feature_layer, 'name', 'Structure Name')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_virtual_dimension(feature_layer, 'length')
        self.set_alias(feature_layer, 'created', 'Created')
        self.set_field_constraint_not_null(feature_layer, 'structure_type_id', 1)
        self.set_created_datetime(feature_layer)

    def configure_complexes(self, feature_layer: QgsVectorLayer) -> None:
        self.set_hidden(feature_layer, 'fid', 'Structure ID')
        self.set_hidden(feature_layer, 'event_id', 'Event ID')
        self.set_alias(feature_layer, 'name', 'Complex Name')
        self.set_multiline(feature_layer, 'initial_condition', 'Initial Conditions')
        self.set_multiline(feature_layer, 'target_condition', 'Target Condition')
        self.set_multiline(feature_layer, 'description', 'Description')
        self.set_virtual_dimension(feature_layer, 'area')
        self.set_created_datetime(feature_layer)

    # QgsActions
    def add_buffer_action(self, feature_layer: QgsVectorLayer, parent_container: QgsAttributeEditorContainer):

        action_text = dedent("""
                            from PyQt5 import QtCore
                            from qgis.PyQt.QtGui import QColor

                            buffers = {"Small":15,
                                    "Large":50}
                            buffer_color = {"Small":QColor(237,10,10,255),
                                            "Large":QColor(237,10,10,255)}
                            preview_layers = {}
                            feats = {}

                            canvas = qgis.utils.iface.mapCanvas()
                            brat_layer = QgsProject.instance().mapLayer('[% @layer_id %]')
                            fid = [% $id %]
                            feature = brat_layer.getFeature(fid)
                            tr = QgsCoordinateTransform(brat_layer.sourceCrs(), QgsCoordinateReferenceSystem("ESRI:102008"), QgsProject.instance())
                            base_geom = feature.geometry()
                            base_geom.transform(tr)

                            for buffer, size in buffers.items():
                                for layer in QgsProject.instance().mapLayersByName(f"QRIS BRAT CIS {buffer} Buffer Context"):
                                    QgsProject.instance().removeMapLayer(layer.id())
                                preview_layers[buffer] = QgsVectorLayer('polygon?crs=esri:102008', f"QRIS BRAT CIS {buffer} Buffer Context", 'memory')
                                # preview_layers[buffer].setFlags(QgsMapLayer.LayerFlag(QgsMapLayer.Private + QgsMapLayer.Removable))
                                preview_layers[buffer].renderer().symbol().symbolLayer(0).setColor(QColor(0,0,0,0))
                                preview_layers[buffer].renderer().symbol().symbolLayer(0).setStrokeColor(buffer_color[buffer])
                                preview_layers[buffer].renderer().symbol().symbolLayer(0).setStrokeStyle(QtCore.Qt.DashLine)
                                preview_layers[buffer].renderer().symbol().symbolLayer(0).setStrokeWidth(0.5)

                                buffer_geom = base_geom.buffer(size, 10, QgsGeometry.CapFlat, QgsGeometry.JoinStyleRound, 0.0)

                                feats[buffer] = QgsFeature()
                                feats[buffer].setGeometry(buffer_geom)
                                preview_layers[buffer].dataProvider().addFeature(feats[buffer])
                                preview_layers[buffer].commitChanges()

                            QgsProject.instance().addMapLayers([layer for layer in preview_layers.values()])
                            tr_extent = QgsCoordinateTransform(QgsCoordinateReferenceSystem("ESRI:102008"),canvas.mapSettings().destinationCrs(), QgsProject.instance())
                            extent_geom = feats['Large'].geometry()
                            extent_geom.transform(tr_extent)
                            canvas.setExtent(extent_geom.boundingBox())
                            canvas.refresh()
                      """).strip("\n")

        action = QgsAction(1, 'Generate Brat CIS Context Buffers', action_text, None, capture=False, shortTitle='Generate Context', actionScopes={'Feature', 'Layer'})
        feature_layer.actions().addAction(action)
        editorAction = QgsAttributeEditorAction(action, parent_container)
        parent_container.addChildElement(editorAction)

    def stop_brat_edit(self):
        buffers = {"Small": 0.0001,
                   "Large": 0.00025}
        for buffer, size in buffers.items():
            for layer in QgsProject.instance().mapLayersByName(f"QRIS BRAT CIS {buffer} Buffer Context"):
                QgsProject.instance().removeMapLayer(layer.id())


def get_comb_expression(database: str, table: str) -> str:

    with sqlite3.connect(database) as conn:
        curs = conn.cursor()
        curs.execute("SELECT * FROM {};".format(table))
        lookup_collection = curs.fetchall()
    expression = "CASE\n"
    for rule in lookup_collection:
        expression += 'WHEN "veg_density_id" = {} AND "base_streampower_id" = {} AND "high_streampower_id" = {} AND "slope_id" = {} THEN {}\n'.format(rule[1], rule[2], rule[3], rule[4], rule[5])
    expression += "ELSE 1\n"
    expression += "END"

    return expression


def get_veg_expression(database: str, table: str) -> str:

    with sqlite3.connect(database) as conn:
        curs = conn.cursor()
        curs.execute("SELECT * FROM {};".format(table))
        lookup_collection = curs.fetchall()
    expression = "CASE\n"
    for rule in lookup_collection:
        expression += 'WHEN "streamside_veg_id" = {} AND "riparian_veg_id" = {} THEN {}\n'.format(rule[1], rule[2], rule[3])
    expression += "ELSE 1\n"
    expression += "END"

    return expression
