-- Database migrations tracking
CREATE TABLE migrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_name TEXT UNIQUE NOT NULL,
  created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- INSERT INTO migrations (file_name) VALUES ('001_initial_schema.sql');
INSERT INTO migrations (file_name) VALUES ('002_raster_change.sql');
INSERT INTO migrations (file_name) VALUES ('003_metrics_update.sql');
INSERT INTO migrations (file_name) VALUES ('004_metadata.sql');
INSERT INTO migrations (file_name) VALUES ('005_raster_symbology.sql');
INSERT INTO migrations (file_name) VALUES ('006_brat_cis_reaches.sql');

-- LOOKUP TABLES
CREATE TABLE protocols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    machine_code TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    has_custom_ui BOOLEAN,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO protocols (id, name, machine_code, has_custom_ui, description) VALUES (1, 'RIM', 'RIM', 0, 'Riverscape Inundation Mapping');
INSERT INTO protocols (id, name, machine_code, has_custom_ui, description) VALUES (2, 'Channel Units', 'CHANNEL_UNITS', 0, 'Simplified channel unit survey for in-channel features. Compliments Low-Tech. Monitoring Protocol');
INSERT INTO protocols (id, name, machine_code, has_custom_ui, description) VALUES (3, 'Active Extents', 'ACTIVE_EXTENT', 0, 'Mapping portions of the valley bottom that are part of the active channel or floodplain');
INSERT INTO protocols (id, name, machine_code, has_custom_ui, description) VALUES (4, 'Low-Tech Design', 'DESIGN', 1, 'Documentation of a design or as-built low-tech structures');
INSERT INTO protocols (id, name, machine_code, has_custom_ui, description) VALUES (5, 'Structural Elements', 'STRUCTURES', 0, 'Survey of primary structural element types');
INSERT INTO protocols (id, name, machine_code, has_custom_ui, description) VALUES (7, 'Beaver Dam Survey', 'BRATCIS', 0, 'Survey of beaver dams');

CREATE TABLE methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    machine_code TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO methods (id, name, machine_code) VALUES (1, 'Dam / Jam Survey', 'DAMJAMS');
INSERT INTO methods (id, name, machine_code) VALUES (2, 'Riverscapes Context', 'RIVERSCAPESCONTEXT');
INSERT INTO methods (id, name, machine_code) VALUES (3, 'Test Orphaned Method', 'WEIRDO');
INSERT INTO methods (id, name, machine_code) VALUES (4, 'BRAT CIS', 'BRATCIS');
INSERT INTO methods (id, name, machine_code) VALUES (5, 'LT-PBR Design', 'LTPBRDESIGN');

CREATE TABLE protocol_methods (
    protocol_id INTEGER NOT NULL REFERENCES protocols(id) ON DELETE CASCADE,
    method_id INTEGER NOT NULL REFERENCES methods(id) ON DELETE CASCADE,

    CONSTRAINT pk_protocol_methods PRIMARY KEY (protocol_id, method_id)
);

INSERT INTO protocol_methods (protocol_id, method_id) VALUES (1, 1);
INSERT INTO protocol_methods (protocol_id, method_id) VALUES (1, 2);
INSERT INTO protocol_methods (protocol_id, method_id) VALUES (2, 2);
INSERT INTO protocol_methods (protocol_id, method_id) VALUES (7, 4);
INSERT INTO protocol_methods (protocol_id, method_id) VALUES (4, 5);


CREATE TABLE layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fc_name TEXT UNIQUE NOT NULL,
    display_name TEXT UNIQUE NOT NULL,
    qml TEXT NOT NULL,
    is_lookup BOOLEAN,
    geom_type TEXT NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Layers
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (1, 'dam_crests', 'Dam Crests', 'Linestring', 0, 'dam_crests.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (3, 'dams', 'Dam Points', 'Point', 0, 'dams.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (4, 'jams', 'Jam Points', 'Point', 0, 'jams.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (5, 'thalwegs', 'Thalwegs', 'Linestring', 0, 'thalwegs.qml', NULL); -- type: primary, secondary - see GUT
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (6, 'active_extents', 'Active Extents', 'Polygon', 0, 'active_extents.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (7, 'centerlines', 'Centerlines', 'Linestring', 0, 'centerlines.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (8, 'inundation_extents', 'Inundation Extents', 'Polygon', 0, 'inundation_extents.qml', NULL); -- type: free flow, overflow, ponded
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (9, 'valley_bottoms', 'Valley Bottoms', 'Polygon', 0, 'valley_bottoms.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (10, 'junctions', 'Junctions', 'Point', 0, 'junctions.qml', NULL); -- type: convergence, divergence
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (11, 'geomorphic_unit_extents', 'Geomorphic Unit Extents', 'Polygon', 0, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (12, 'geomorphic_units', 'Geomorphic Unit Points', 'Point', 0, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (13, 'geomorphic_units_tier3', 'Tier 3 Geomorphic Units', 'Point', 0, 'temp.qml', NULL); -- fluvial taxonomy
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (14, 'cem_phases', 'Channel Evolution Model Stages', 'Polygon', 0, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (15, 'vegetation_extents', 'Vegetation Extents', 'Polygon', 0, 'temp.qml', NULL); -- veg_classes
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (16, 'floodplain_accessibilities', 'Floodplain Accessibility', 'Polygon', 0, 'temp.qml', NULL); -- floating point accessibility
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (17, 'brat_vegetation', 'Brat Vegetation Suitability', 'Polygon', 0, 'temp.qml', NULL);
-- INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (18, 'designs', 'Design', 'NoGeometry', 0, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (19, 'zoi', 'Zones of influence', 'Polygon', 0, 'zoi.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (20, 'complexes', 'Structure Complex Extents', 'Polygon', 0, 'complexes.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (21, 'structure_points', 'Structure Points', 'Point', 0, 'structure_points.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (22, 'structure_lines', 'Structure Lines', 'Linestring', 0, 'structure_lines.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (23, 'channel_unit_points', 'Channel Unit Points', 'Point', 0, 'channel_unit_points.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (24, 'channel_unit_polygons', 'Channel Unit Polygons ', 'Polygon', 0, 'channel_unit_polygons.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (25, 'brat_cis', 'BRAT CIS (Capacity Inference System)', 'Point', 0, 'none.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (26, 'brat_cis_reaches', 'BRAT CIS Reaches', 'Linestring', 0, 'brat_reaches_manual.qml', NULL);
-- Lookup Tables
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (100, 'lkp_metric_sources', 'Metric Sources', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (101, 'lkp_platform', 'Platform', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (102, 'lkp_mask_types', 'Mask Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (103, 'lkp_structure_source', 'Structure Sources', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (104, 'lkp_dam_integrity', 'Dam Integrity', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (105, 'lkp_beaver_maintenance', 'Beaver Maintenance', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (106, 'lkp_thalweg_types', 'Thalweg Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (107, 'lkp_active_extent_types', 'Active Extent Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (108, 'lkp_junction_types', 'Junction Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (109, 'lkp_geomorphic_unit_types', 'Geomorphic Unit Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (110, 'lkp_vegetation_extent_types', 'Vegetation Extent Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (111, 'lkp_cem_phase_types', 'CEM Phase Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (112, 'lkp_floodplain_accessibility_types', 'Floodplain Accessibility Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (113, 'lkp_brat_vegetation_types', 'Brat Vegetation Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (114, 'lkp_context_layer_types', 'Context Layer Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (115, 'lkp_inundation_extent_types', 'Inundation Extent Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (116, 'lkp_primary_channel', 'Primary Channel Type', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (117, 'lkp_primary_unit', 'Primary Unit Type', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (118, 'lkp_structure_forced', 'Structure Forced', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (119, 'lkp_channel_unit_types', 'Channel Unit Types', 'NoGeometry', 1, 'temp.qml', NULL);

INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (120, 'lkp_design_status', 'Design Status', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (121, 'lkp_structure_mimics', 'Structure Mimics', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (122, 'lkp_zoi_stage', 'ZOI Stage', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (123, 'structure_types', 'Structure Types', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (124, 'zoi_types', 'Zoi Types', 'NoGeometry', 1, 'temp.qml', NULL);

INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (125, 'lkp_brat_base_streampower', 'Base Streampower', 'NoGeometry', 1, 'temp.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (126, 'lkp_brat_high_streampower', 'High flow Streampower', 'NoGeometry', 1, 'none.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (127, 'lkp_brat_slope', 'Slope', 'NoGeometry', 1, 'none.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (128, 'lkp_brat_dam_density', 'BRAT Dam Density', 'NoGeometry', 1, 'none.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (129, 'lkp_brat_vegetation_cis', 'BRAT Vegetation CIS', 'NoGeometry', 1, 'none.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (130, 'lkp_brat_combined_cis', 'BRAT Combined CIS', 'NoGeometry', 1, 'none.qml', NULL);

INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (131, 'lkp_representation', 'Representation', 'NoGeometry', 1, 'temp.qml', NULL);
-- INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (132, 'lkp_profiles', 'Profiles', 'NoGeometry', 1, 'none.qml', NULL);
INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (133, 'lkp_units', 'Unit Types', 'NoGeometry', 1, 'none.qml', NULL);

CREATE TABLE method_layers (
    method_id INTEGER NOT NULL REFERENCES methods(id) ON DELETE CASCADE,
    layer_id INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,

    CONSTRAINT pk_method_layers PRIMARY KEY (method_id, layer_id)
);

INSERT INTO method_layers (method_id, layer_id) VALUES (1, 1);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 3);
INSERT INTO method_layers (method_id, layer_id) VALUES (1, 4);
INSERT INTO method_layers (method_id, layer_id) VALUES (2, 9);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 9);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 25);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 26);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 19);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 20);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 21);
INSERT INTO method_layers (method_id, layer_id) VALUES (5, 22);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 5);
INSERT INTO method_layers (method_id, layer_id) VALUES (3, 7);

-- CREATE TABLE protocol_layers (
--     protocol_id INTEGER NOT NULL REFERENCES protocols(id) ON DELETE CASCADE,
--     layer_id INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE,
--     metadata TEXT,
--     CONSTRAINT pk_protocol_layers PRIMARY KEY (protocol_id, layer_id)
-- );

-- -- RIM
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (1, 1);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (1, 5);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (1, 8);

-- -- Active Extents
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (2, 6);

-- -- Structural Elements
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (4, 3);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (4, 4);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (4, 1);

-- -- Low Tech Designs
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (3, 19);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (3, 20);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (3, 21);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (3, 22);

-- -- Channel Units
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (6, 23);
-- INSERT INTO protocol_layers (protocol_id, layer_id) VALUES (6, 24);

CREATE TABLE lkp_metric_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_metric_sources (id, name, description) VALUES (1, 'Calculated', 'Calculated from spatial data');
INSERT INTO lkp_metric_sources (id, name, description) VALUES (2, 'Estimated', 'Estimated from other sources or evidence');


CREATE TABLE lkp_context_layer_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    symbology TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (1, 'Aerial imagery', NULL);
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (2, 'DEM', 'Shared/dem.qml');
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (3, 'Detrended DEM', NULL);
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (4, 'Geomorphic Change Detection (GCD)',NULL);
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (5, 'Hillshade', 'Shared/Hillshade.qml');
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (6, 'Slope Raster','Shared/slope.qml');
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (7, 'VBET Evidence','VBET/vbetLikelihood.qml');
INSERT INTO lkp_context_layer_types (id, name, symbology) VALUES (8, 'Other', NULL);

-- so, can these be vector and raster? does it matter?
CREATE TABLE context_layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id INTEGER REFERENCES lkp_context_layer_types(id),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    path TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    map_guid TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_by TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lkp_event_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

INSERT INTO lkp_event_types (id, name, description) VALUES (1, 'Generic Data Capture Event', NULL);
INSERT INTO lkp_event_types (id, name, description) VALUES (2, 'Low Tech Design', NULL);
INSERT INTO lkp_event_types (id, name, description) VALUES (3, 'As-Built survey', NULL);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    event_type_id INT REFERENCES lkp_event_types(id),
    platform_id INTEGER REFERENCES lkp_platform(id),
    representation_id INTEGER REFERENCES lkp_representation(id),
    metadata TEXT,
    date_text TEXT,
    start_year INT,
    start_month INT,
    start_day INT,
    end_year INT,
    end_month INT,
    end_day INT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lkp_platform (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_platform (id, name) VALUES (1, 'Desktop');
INSERT INTO lkp_platform (id, name) VALUES (2, 'Field');

CREATE TABLE lkp_representation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_representation (id, name) VALUES (1, 'Current');
INSERT INTO lkp_representation (id, name) VALUES (2, 'Historic');
INSERT INTO lkp_representation (id, name) VALUES (3, 'Future');

CREATE TABLE event_layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    layer_id INTEGER NOT NULL REFERENCES layers(id) ON DELETE CASCADE
);
CREATE UNIQUE index ux_event_layers ON event_layers(event_id, layer_id);

CREATE TABLE lkp_raster_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    symbology TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_raster_types (id, name, symbology) VALUES (1, 'Other', NULL);
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (2, 'Basemap', NULL);
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (3, 'Detrended Surface', NULL);
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (4, 'Digital Elevation Model (DEM)', 'Shared/dem.qml');
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (5, 'Valley Bottom Evidence', 'VBET/vbetLikelihood.qml');
INSERT INTO lkp_raster_types (id, name, symbology) VALUES (6, 'Hillshade', 'Shared/Hillshade.qml');


CREATE TABLE rasters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raster_type_id INTEGER REFERENCES lkp_raster_types(id),
    is_context Boolean DEFAULT 0,
    name TEXT UNIQUE NOT NULL,
    path TEXT UNIQUE NOT NULL,
    -- type will likely be populated from a lookup. e.g., imagery, dem, lidar, etc....
    type TEXT,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX fx_rasters_raster_type_id ON rasters(raster_type_id);


CREATE TABLE lkp_scratch_vector_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_scratch_vector_types (id, name) VALUES (1, 'Other');

CREATE TABLE scratch_vectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vector_type_id INTEGER REFERENCES lkp_scratch_vector_types(id),
    name TEXT UNIQUE NOT NULL,
    fc_name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX fx_scratch_vectors_vector_type_id ON scratch_vectors(vector_type_id);


CREATE TABLE event_rasters (
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    raster_id INTEGER REFERENCES rasters(id) ON DELETE CASCADE,
    
    CONSTRAINT pk_event_rasters PRIMARY KEY (event_id, raster_id)
);

CREATE TABLE lkp_mask_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- need to review these types. I'm not totally sure that this is necessary in a table.
INSERT INTO lkp_mask_types (id, name) VALUES (1, 'Area of Interest (AOI)');
INSERT INTO lkp_mask_types (id, name) VALUES (2, 'Regular Mask');
INSERT INTO lkp_mask_types (id, name) VALUES (3, 'Directional Mask');

CREATE TABLE masks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    mask_type_id INTEGER NOT NULL REFERENCES lkp_mask_types(id),
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- AOI features refer to the AOI mask that they belong to
ALTER TABLE aoi_features ADD COLUMN mask_id INTEGER REFERENCES masks(id) ON DELETE CASCADE;
ALTER TABLE aoi_features ADD COLUMN metadata TEXT;

-- Regular masks refer to the mask that they belong to and have a display label
ALTER TABLE mask_features ADD COLUMN mask_id INTEGER REFERENCES masks(id) ON DELETE CASCADE;
ALTER TABLE mask_features ADD COLUMN display_label TEXT;
ALTER TABLE mask_features ADD COLUMN display_order INTEGER;
-- ALTER TABLE mask_features ADD COLUMN name TEXT;
ALTER TABLE mask_features ADD COLUMN position INTEGER;
ALTER TABLE mask_features ADD COLUMN description TEXT;
ALTER TABLE mask_features ADD COLUMN metadata TEXT;

-- units
CREATE TABLE lkp_units (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL UNIQUE,
	display_name TEXT NOT NULL UNIQUE,
	conversion REAL,
	conversion_unit_id INTEGER,
	dimension TEXT,
	description TEXT,
    metatdata TEXT,
	created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (1, 'Meters', 'm', NULL, NULL, 'length');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (2, 'Square Meters', '㎡', NULL, NULL, 'area');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (3, 'Cubic Meters', 'm³', NULL, NULL, 'volume');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (4, 'Feet', 'ft', 0.3048, 1, 'length');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (5, 'Square Feet', 'sqft', 0.092903, 2, 'area');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (6, 'Cubic Feet', 'ft³', 0.0283168, 3, 'volume');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (7, 'Hectares', 'ha', 10000, 2, 'area');
INSERT INTO lkp_units (id, name, display_name, conversion, conversion_unit_id, dimension) VALUES (8, 'Acres', 'ac', 4046.86, 2, 'area');

CREATE TABLE calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_function TEXT
);

INSERT INTO calculations (id, name, metric_function) VALUES (1, 'count', 'count');
INSERT INTO calculations (id, name, metric_function) VALUES (2, 'length', 'length');
INSERT INTO calculations (id, name, metric_function) VALUES (3, 'area', 'area');
INSERT INTO calculations (id, name, metric_function) VALUES (4, 'sinuosity', 'sinuosity');
INSERT INTO calculations (id, name, metric_function) VALUES (5, 'gradient', 'gradient');

CREATE TABLE metric_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

INSERT INTO metric_levels (id, name) VALUES (1, 'Metric');
INSERT INTO metric_levels (id, name) VALUES (2, 'Indicator');


CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_id INTEGER REFERENCES calculations(id),
    default_level_id INTEGER REFERENCES metric_levels(id),
    unit_id INTEGER REFERENCES lkp_units(id),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    definition_url TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_params TEXT
);

INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (1, 1, 'dam and jam count', 1, NULL, '{"layers": ["dams","jams"]}', '{"min_value": 0}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (2, NULL, 'Percent Active Floodplain', 1, NULL, NULL, '{"min_value": 0, "max_value": 100, "tolerance": 0.25}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (3, 5, 'Centerline Gradient', 2, NULL, '{"layers": ["profile_centerlines"], "rasters": ["Digital Elevation Model (DEM)"]}', '{"precision": 4, "tolerance": 0.1}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (4, 2, 'Dam Crest Length', 1, 1, '{"layers": ["dam_crests"]}', '{"min_value": 0, "max_value": 10000, "precision": 2, "tolerance": 0.1}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (5, 3, 'Valley Bottom Area', 1, 2, '{"layers": ["valley_bottoms"]}', NULL);
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (6, 4, 'Centelrine Sinuosity', 1,  NULL, '{"layers": ["profile_centerlines"]}', '{"min_value": 1, "precision": 4, "tolerance": 0.1}');

CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    mask_id INTEGER NOT NULL REFERENCES masks(id),
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX fx_analyses_mask_id ON analyses(mask_id);

CREATE TABLE analysis_metrics (
    analysis_id INT NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    metric_id INT NOT NULL REFERENCES metrics(id),
    level_id INT NOT NULL REFERENCES metric_levels(id),

    CONSTRAINT pk_analysis_metrics PRIMARY KEY (analysis_id, metric_id)
);


CREATE TABLE metric_values (
    analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
    mask_feature_id INTEGER REFERENCES mask_features(fid) ON DELETE CASCADE,
    metric_id INTEGER REFERENCES metrics(id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
--     metric_source_id INTEGER REFERENCES metric_sources(id) ON DELETE CASCADE,
    manual_value NUMERIC,
    automated_value NUMERIC,
    is_manual INT NOT NULL DEFAULT 1,
    metadata TEXT,
    description TEXT,
    uncertainty NUMERIC,
    unit_id INTEGER REFERENCES lkp_units(id),
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_metric_values PRIMARY KEY (analysis_id, event_id, mask_feature_id, metric_id)
);

CREATE INDEX fx_metric_values_analysis_id ON metric_values(analysis_id);
CREATE INDEX fx_metric_values_mask_feature_id ON metric_values(mask_feature_id);
CREATE INDEX fx_metric_values_metric_id ON metric_values(metric_id);
CREATE INDEX fx_metric_values_event_id ON metric_values(event_id);

-- dam and jam surveys
CREATE TABLE lkp_structure_source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_structure_source (id, name) VALUES (1, 'Natural');
INSERT INTO lkp_structure_source (id, name) VALUES (2, 'Artificial');
INSERT INTO lkp_structure_source (id, name) VALUES (3, 'Unknown');


CREATE TABLE lkp_dam_integrity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_dam_integrity (id, name) VALUES (1, 'Intact');
INSERT INTO lkp_dam_integrity (id, name) VALUES (3, 'Blown');
INSERT INTO lkp_dam_integrity (id, name) VALUES (2, 'Breached');
INSERT INTO lkp_dam_integrity (id, name) VALUES (4, 'Buried');
INSERT INTO lkp_dam_integrity (id, name) VALUES (5, 'Flooded');
INSERT INTO lkp_dam_integrity (id, name) VALUES (6, 'NA');

CREATE TABLE lkp_beaver_maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_beaver_maintenance (id, name) VALUES (1, 'None');
INSERT INTO lkp_beaver_maintenance (id, name) VALUES (2, 'Old');
INSERT INTO lkp_beaver_maintenance (id, name) VALUES (3, 'Fresh');
INSERT INTO lkp_beaver_maintenance (id, name) VALUES (4, 'NA');


-- dam crests
ALTER TABLE dam_crests ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE dam_crests ADD COLUMN structure_source_id INTEGER REFERENCES lkp_structure_source(id);
ALTER TABLE dam_crests ADD COLUMN dam_integrity_id INTEGER REFERENCES lkp_dam_integrity(id);
ALTER TABLE dam_crests ADD COLUMN beaver_maintenance_id INTEGER REFERENCES lkp_beaver_maintenance(id);
ALTER TABLE dam_crests ADD description TEXT;
ALTER TABLE dam_crests ADD COLUMN metadata TEXT;

-- dam points
ALTER TABLE dams ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE dams ADD COLUMN structure_source_id INTEGER REFERENCES lkp_structure_source(id);
ALTER TABLE dams ADD COLUMN dam_integrity_id INTEGER REFERENCES lkp_dam_integrity(id);
ALTER TABLE dams ADD COLUMN beaver_maintenance_id INTEGER REFERENCES lkp_beaver_maintenance(id);
ALTER TABLE dams ADD COLUMN length NUMERIC;
ALTER TABLE dams ADD COLUMN height NUMERIC;
ALTER TABLE dams ADD description TEXT;
ALTER TABLE dams ADD COLUMN metadata TEXT;

-- jam points
ALTER TABLE jams ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE jams ADD COLUMN structure_source_id INTEGER REFERENCES lkp_structure_source(id);
ALTER TABLE jams ADD COLUMN beaver_maintenance_id INTEGER REFERENCES lkp_beaver_maintenance(id);
ALTER TABLE jams ADD COLUMN length NUMERIC;
ALTER TABLE jams ADD COLUMN width NUMERIC;
ALTER TABLE jams ADD COLUMN height NUMERIC;
ALTER TABLE jams ADD COLUMN wood_count INTEGER;
ALTER TABLE jams ADD description TEXT;
ALTER TABLE jams ADD COLUMN metadata TEXT;

-- thalwegs
CREATE TABLE lkp_thalweg_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_thalweg_types (id, name) VALUES (1, 'Primary');
INSERT INTO lkp_thalweg_types (id, name) VALUES (2, 'Non-Primary');

ALTER TABLE thalwegs ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE thalwegs ADD COLUMN type_id INTEGER REFERENCES lkp_thalweg_types(id);
ALTER TABLE thalwegs ADD description TEXT;

-- active extents
CREATE TABLE lkp_active_extent_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_active_extent_types (id, name) VALUES (1, 'Active');
INSERT INTO lkp_active_extent_types (id, name) VALUES (2, 'Inactive');

ALTER TABLE active_extents ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE active_extents ADD COLUMN type_id INTEGER REFERENCES lkp_active_extent_types(id);
ALTER TABLE active_extents ADD description TEXT;
ALTER TABLE active_extents ADD metadata TEXT;

-- centerlines
ALTER TABLE centerlines ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE centerlines ADD COLUMN metadata TEXT;

-- inundation
CREATE TABLE lkp_inundation_extent_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_inundation_extent_types (id, name) VALUES (1, 'Free Flowing');
INSERT INTO lkp_inundation_extent_types (id, name) VALUES (2, 'Ponded');
INSERT INTO lkp_inundation_extent_types (id, name) VALUES (3, 'Overflow');

ALTER TABLE inundation_extents ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE inundation_extents ADD COLUMN type_id INTEGER REFERENCES lkp_inundation_extent_types(id);
ALTER TABLE inundation_extents ADD description TEXT;
ALTER TABLE inundation_extents ADD metadata TEXT;

-- valley bottoms
ALTER TABLE valley_bottoms ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE valley_bottoms ADD COLUMN metadata TEXT;

-- junctions
CREATE TABLE lkp_junction_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_junction_types (id, name) VALUES (1, 'Confluence');
INSERT INTO lkp_junction_types (id, name) VALUES (2, 'Diffluence');

ALTER TABLE junctions ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE junctions ADD COLUMN type_id INTEGER REFERENCES lkp_junction_types(id) ON DELETE CASCADE;
ALTER TABLE junctions ADD COLUMN metadata TEXT;

-- geomorphic units
CREATE TABLE lkp_geomorphic_unit_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_geomorphic_unit_types (id, name) VALUES (1, 'Concavity');
INSERT INTO lkp_geomorphic_unit_types (id, name) VALUES (2, 'Convexity');
INSERT INTO lkp_geomorphic_unit_types (id, name) VALUES (3, 'Planner');
INSERT INTO lkp_geomorphic_unit_types (id, name) VALUES (4, 'Pond');

ALTER TABLE geomorphic_units ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE geomorphic_units ADD COLUMN type_id INTEGER REFERENCES lkp_geomorphic_unit_types(id);
ALTER TABLE geomorphic_units ADD COLUMN metadata TEXT;

ALTER TABLE geomorphic_unit_extents ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE geomorphic_unit_extents ADD COLUMN type_id INTEGER REFERENCES lkp_geomorphic_unit_types(id);
ALTER TABLE geomorphic_unit_extents ADD COLUMN metadata TEXT;

ALTER TABLE geomorphic_units_tier3 ADD COLUMN metadata TEXT;

-- cem phases
CREATE TABLE lkp_cem_phase_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_cem_phase_types (id, name) VALUES (1, 'Stage-1');
INSERT INTO lkp_cem_phase_types (id, name) VALUES (2, 'Stage-5');
INSERT INTO lkp_cem_phase_types (id, name) VALUES (3, 'Stage-0');

ALTER TABLE cem_phases ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE cem_phases ADD COLUMN type_id INTEGER REFERENCES lkp_cem_phase_types(id);
ALTER TABLE cem_phases ADD COLUMN metadata TEXT;

-- vegetation extents
CREATE TABLE lkp_vegetation_extent_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_vegetation_extent_types (id, name) VALUES (1, 'Riparian');
INSERT INTO lkp_vegetation_extent_types (id, name) VALUES (2, 'Wetland');
INSERT INTO lkp_vegetation_extent_types (id, name) VALUES (3, 'Upland');
INSERT INTO lkp_vegetation_extent_types (id, name) VALUES (4, 'Other');

ALTER TABLE vegetation_extents ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE vegetation_extents ADD COLUMN type_id INTEGER REFERENCES lkp_vegetation_extent_types(id);
ALTER TABLE vegetation_extents ADD COLUMN metadata TEXT;

-- floodplain acessibility
CREATE TABLE lkp_floodplain_accessibility_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_floodplain_accessibility_types (id, name) VALUES (1, 'Inaccessible');
INSERT INTO lkp_floodplain_accessibility_types (id, name) VALUES (2, 'Surface water Accessible');
INSERT INTO lkp_floodplain_accessibility_types (id, name) VALUES (3, 'Groundwater Accessible');
INSERT INTO lkp_floodplain_accessibility_types (id, name) VALUES (4, 'Fully Accessible');

ALTER TABLE floodplain_accessibilities ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE floodplain_accessibilities ADD COLUMN type_id INTEGER REFERENCES lkp_floodplain_accessibility_types(id);
ALTER TABLE floodplain_accessibilities ADD COLUMN metadata TEXT;

-- brat vegetation
CREATE TABLE lkp_brat_vegetation_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (1, 'Preferred');
INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (2, 'Suitable');
INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (3, 'Moderately Suitable');
INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (4, 'Barely Suitable');
INSERT INTO lkp_brat_vegetation_types (id, name) VALUES (5, 'Unsuitable');

ALTER TABLE brat_vegetation ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE brat_vegetation ADD COLUMN type_id INTEGER REFERENCES lkp_brat_vegetation_types(id) ON DELETE CASCADE;
ALTER TABLE brat_vegetation ADD COLUMN metadata TEXT;

-- BRAT base Stream power
CREATE TABLE lkp_brat_base_streampower (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_brat_base_streampower (id, name) VALUES (1, 'Probably can build dam');
INSERT INTO lkp_brat_base_streampower (id, name) VALUES (2, 'Can build dam');
INSERT INTO lkp_brat_base_streampower (id, name) VALUES (3, 'Can build dam (saw evidence of recent dams)');
INSERT INTO lkp_brat_base_streampower (id, name) VALUES (4, 'Could build dam at one time (saw evidence of relic dams)');
INSERT INTO lkp_brat_base_streampower (id, name) VALUES (5, 'Cannot build dam (streampower really high)');

-- BRAT 2 year flood stream power
CREATE TABLE lkp_brat_high_streampower (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_brat_high_streampower (id, name) VALUES (1, 'Blowout');
INSERT INTO lkp_brat_high_streampower (id, name) VALUES (2, 'Occasional Breach');
INSERT INTO lkp_brat_high_streampower (id, name) VALUES (3, 'Occasional Blowout');
INSERT INTO lkp_brat_high_streampower (id, name) VALUES (4, 'Dam Persists');


CREATE TABLE lkp_brat_slope (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_brat_slope (id, name) VALUES (1, 'So steep they cannot build a dam (e.g. > 20% slope)');
INSERT INTO lkp_brat_slope (id, name) VALUES (2, 'Probably can build dam');
INSERT INTO lkp_brat_slope (id, name) VALUES (3, 'Can build dam (inferred)');
INSERT INTO lkp_brat_slope (id, name) VALUES (4, 'Can build dam (evidence or current or past dams)');
INSERT INTO lkp_brat_slope (id, name) VALUES (5, 'Really flat (can build dam, but might not need as many as one dam might back up water > 0.5 km)');

CREATE TABLE lkp_brat_dam_density (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (1, 'None', '(no dams)');
INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (2, 'Rare', '(0-1 dams/km)');
INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (3, 'Occasional', '(1-4 dams/km)');
INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (4, 'Frequent', '(5-15 dams/km)');
INSERT INTO lkp_brat_dam_density (id, name, description) VALUES (5, 'Pervasive', '(15-40 dams/km)');

CREATE TABLE lkp_brat_vegetation_cis
(
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT ,
    streamside_veg_id INT NOT NULL REFERENCES lkp_brat_vegetation_types (id) ON DELETE CASCADE,
    riparian_veg_id INT NOT NULL REFERENCES  lkp_brat_vegetation_types (id) ON DELETE CASCADE,
    output_id INT NOT NULL REFERENCES lkp_brat_dam_density(id) ON DELETE CASCADE
);
CREATE INDEX ux_lkp_brat_vegetation_cis ON lkp_brat_vegetation_cis(streamside_veg_id, riparian_veg_id, output_id);

INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (1, 5, 5, 1);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (2, 4, 5, 2);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (3, 3, 5, 3);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (4, 2, 5, 3);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (5, 1, 5, 3);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (6, 5, 4, 2);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (7, 4, 4, 3);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (8, 3, 4, 3);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (9, 2, 4, 4);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (10, 1, 4, 4);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (11, 5, 3, 3);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (12, 4, 3, 2);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (13, 3, 3, 4);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (14, 2, 3, 4);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (15, 1, 3, 5);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (16, 5, 2, 2);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (17, 4, 2, 4);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (18, 3, 2, 4);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (19, 2, 2, 4);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (20, 1, 2, 5);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (21, 5, 1, 3);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (22, 4, 1, 4);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (23, 3, 1, 4);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (24, 2, 1, 5);
INSERT INTO lkp_brat_vegetation_cis (rule_id, streamside_veg_id, riparian_veg_id, output_id) VALUES (25, 1, 1, 5);

CREATE TABLE lkp_brat_combined_cis (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    veg_density_id INTEGER NOT NULL REFERENCES lkp_brat_vegetation_cis(rule_id) ON DELETE CASCADE,
    base_streampower_id INTEGER NOT NULL REFERENCES lkp_brat_base_streampower(id) ON DELETE CASCADE,
    high_streampower_id INTEGER NOT NULL REFERENCES lkp_brat_high_streampower(id) ON DELETE CASCADE,
    slope_id INTEGER NOT NULL REFERENCES  lkp_brat_slope(id) ON DELETE CASCADE,
    output_id INTEGER NOT NULL REFERENCES lkp_brat_dam_density(id) ON DELETE CASCADE
);
CREATE INDEX ux_lkp_brat_combined_cis ON lkp_brat_combined_cis(veg_density_id, base_streampower_id, high_streampower_id, slope_id);

--value combinations that produce an output of 'None' are not stored in this table
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (1, 2, 2, 4, 1, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (2, 2, 2, 4, 2, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (3, 2, 2, 4, 3, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (4, 2, 2, 4, 4, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (5, 2, 2, 4, 5, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (6, 3, 2, 4, 1, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (7, 3, 2, 4, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (8, 3, 2, 4, 3, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (9, 3, 2, 4, 4, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (10, 3, 2, 4, 5, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (11, 4, 2, 4, 4, 4);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (12, 4, 2, 4, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (13, 5, 2, 4, 5, 5);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (14, 5, 2, 4, 4, 5);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (15, 5, 2, 4, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (16, 2, 2, 2, 1, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (17, 2, 2, 2, 2, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (18, 2, 2, 2, 3, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (19, 2, 2, 2, 4, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (20, 2, 2, 2, 5, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (21, 3, 2, 2, 1, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (22, 3, 2, 2, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (23, 3, 2, 2, 3, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (24, 3, 2, 2, 4, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (25, 3, 2, 2, 5, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (26, 4, 2, 2, 4, 4);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (27, 4, 2, 2, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (28, 5, 2, 2, 5, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (29, 5, 2, 2, 4, 4);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (30, 5, 2, 2, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (31, 2, 2, 3, 1, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (32, 2, 2, 3, 2, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (33, 2, 2, 3, 3, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (34, 2, 2, 3, 4, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (35, 2, 2, 3, 5, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (36, 3, 2, 3, 1, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (37, 3, 2, 3, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (38, 3, 2, 3, 3, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (39, 3, 2, 3, 4, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (40, 3, 2, 3, 5, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (41, 4, 2, 3, 4, 4);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (42, 4, 2, 3, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (43, 5, 2, 3, 5, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (44, 5, 2, 3, 4, 4);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (45, 5, 2, 3, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (46, 3, 2, 1, 1, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (47, 3, 2, 1, 2, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (48, 3, 2, 1, 3, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (49, 3, 2, 1, 4, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (50, 3, 2, 1, 5, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (51, 4, 2, 1, 4, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (52, 5, 2, 1, 5, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (53, 5, 2, 1, 4, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (54, 5, 2, 1, 2, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (55, 2, 1, 2, 1, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (56, 2, 1, 2, 2, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (57, 2, 1, 2, 3, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (58, 2, 1, 2, 4, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (59, 2, 1, 2, 5, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (60, 3, 1, 2, 1, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (61, 3, 1, 2, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (62, 3, 1, 2, 3, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (63, 3, 1, 2, 4, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (64, 3, 1, 2, 5, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (65, 4, 1, 2, 4, 4);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (66, 4, 1, 2, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (67, 5, 1, 2, 5, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (68, 5, 1, 2, 4, 4);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (69, 5, 1, 2, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (70, 2, 1, 3, 1, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (71, 2, 1, 3, 2, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (72, 2, 1, 3, 3, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (73, 2, 1, 3, 4, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (74, 2, 1, 3, 5, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (75, 3, 1, 3, 1, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (76, 3, 1, 3, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (77, 3, 1, 3, 3, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (78, 3, 1, 3, 4, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (79, 3, 1, 3, 5, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (80, 4, 1, 3, 4, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (81, 4, 1, 3, 2, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (82, 5, 1, 3, 5, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (83, 5, 1, 3, 4, 4);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (84, 5, 1, 3, 2, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (85, 3, 1, 1, 1, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (86, 3, 1, 1, 2, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (87, 3, 1, 1, 3, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (88, 3, 1, 1, 4, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (89, 3, 1, 1, 5, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (90, 4, 1, 1, 4, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (91, 5, 1, 1, 5, 2);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (92, 5, 1, 1, 4, 3);
INSERT INTO lkp_brat_combined_cis (rule_id, veg_density_id, base_streampower_id, high_streampower_id, slope_id, output_id) VALUES (93, 5, 1, 1, 2, 2);

-- Alter the BRAT CIS Feature Class table
ALTER TABLE brat_cis ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE brat_cis ADD COLUMN observer_name TEXT;
ALTER TABLE brat_cis ADD COLUMN reach_id TEXT;
ALTER TABLE brat_cis ADD COLUMN observation_date DATE;
ALTER TABLE brat_cis ADD COLUMN reach_length FLOAT;
ALTER TABLE brat_cis ADD COLUMN notes TEXT;
ALTER TABLE brat_cis ADD COLUMN metadata TEXT;

ALTER TABLE brat_cis ADD COLUMN streamside_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
ALTER TABLE brat_cis ADD COLUMN riparian_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
ALTER TABLE brat_cis ADD COLUMN veg_density_id INT REFERENCES lkp_brat_dam_density(id);

ALTER TABLE brat_cis ADD COLUMN base_streampower_id INT REFERENCES lkp_brat_base_streampower(id);
ALTER TABLE brat_cis ADD COLUMN high_streampower_id INT REFERENCES lkp_brat_high_streampower(id);

ALTER TABLE brat_cis ADD COLUMN slope_id INT REFERENCES lkp_brat_slope(id);

ALTER TABLE brat_cis ADD COLUMN combined_density_id INT REFERENCES lkp_brat_dam_density(id);

-- Alter the Brat CIS Reaches feature class
ALTER TABLE brat_cis_reaches ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE brat_cis_reaches ADD COLUMN observer_name TEXT;
ALTER TABLE brat_cis_reaches ADD COLUMN reach_id TEXT;
ALTER TABLE brat_cis_reaches ADD COLUMN observation_date DATE;
ALTER TABLE brat_cis_reaches ADD COLUMN reach_length FLOAT;
ALTER TABLE brat_cis_reaches ADD COLUMN notes TEXT;
ALTER TABLE brat_cis_reaches ADD COLUMN metadata TEXT;

ALTER TABLE brat_cis_reaches ADD COLUMN streamside_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
ALTER TABLE brat_cis_reaches ADD COLUMN riparian_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
ALTER TABLE brat_cis_reaches ADD COLUMN veg_density_id INT REFERENCES lkp_brat_dam_density(id);

ALTER TABLE brat_cis_reaches ADD COLUMN base_streampower_id INT REFERENCES lkp_brat_base_streampower(id);
ALTER TABLE brat_cis_reaches ADD COLUMN high_streampower_id INT REFERENCES lkp_brat_high_streampower(id);

ALTER TABLE brat_cis_reaches ADD COLUMN slope_id INT REFERENCES lkp_brat_slope(id);

ALTER TABLE brat_cis_reaches ADD COLUMN combined_density_id INT REFERENCES lkp_brat_dam_density(id);
----------------------------------------------------------------------------------------------------------------

-- channel unit layers
CREATE TABLE lkp_channel_unit_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_channel_unit_types (id, name) VALUES (1, 'Concavity');
INSERT INTO lkp_channel_unit_types (id, name) VALUES (2, 'Convexity');
INSERT INTO lkp_channel_unit_types (id, name) VALUES (3, 'Planar');
INSERT INTO lkp_channel_unit_types (id, name) VALUES (4, 'Pond');
INSERT INTO lkp_channel_unit_types (id, name) VALUES (5, 'NA');


CREATE TABLE lkp_structure_forced (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_structure_forced (id, name) VALUES (1, 'Artificial Structure');
INSERT INTO lkp_structure_forced (id, name) VALUES (2, 'Natural Structure');
INSERT INTO lkp_structure_forced (id, name) VALUES (3, 'Not Structure Forced');
INSERT INTO lkp_structure_forced (id, name) VALUES (4, 'NA');


CREATE TABLE lkp_primary_channel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_primary_channel (id, name) VALUES (1, 'Primary Channel');
INSERT INTO lkp_primary_channel (id, name) VALUES (2, 'Non-Primary Channel');
INSERT INTO lkp_primary_channel (id, name) VALUES (3, 'NA');

CREATE TABLE lkp_primary_unit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_primary_unit (id, name) VALUES (1, 'Primary Unit');
INSERT INTO lkp_primary_unit (id, name) VALUES (2, 'Non-Primary Unit');
INSERT INTO lkp_primary_unit (id, name) VALUES (3, 'NA');


ALTER TABLE channel_unit_points ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_points ADD COLUMN unit_type_id INTEGER REFERENCES lkp_channel_unit_types(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_points ADD COLUMN structure_forced_id INTEGER REFERENCES lkp_structure_forced(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_points ADD COLUMN primary_unit_id INTEGER REFERENCES lkp_primary_unit(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_points ADD COLUMN primary_channel_id INTEGER REFERENCES lkp_primary_channel(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_points ADD COLUMN length NUMERIC;
ALTER TABLE channel_unit_points ADD COLUMN width NUMERIC;
ALTER TABLE channel_unit_points ADD COLUMN depth NUMERIC;
ALTER TABLE channel_unit_points ADD COLUMN percent_wetted NUMERIC;
ALTER TABLE channel_unit_points ADD COLUMN description TEXT;
ALTER TABLE channel_unit_points ADD COLUMN metadata TEXT;


ALTER TABLE channel_unit_polygons ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_polygons ADD COLUMN unit_type_id INTEGER REFERENCES lkp_channel_unit_types(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_polygons ADD COLUMN structure_forced_id INTEGER REFERENCES lkp_structure_forced(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_polygons ADD COLUMN primary_unit_id INTEGER REFERENCES lkp_primary_unit(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_polygons ADD COLUMN primary_channel_id INTEGER REFERENCES lkp_primary_channel(id) ON DELETE CASCADE;
ALTER TABLE channel_unit_polygons ADD COLUMN percent_wetted NUMERIC;
ALTER TABLE channel_unit_polygons ADD COLUMN description TEXT;
ALTER TABLE channel_unit_polygons ADD COLUMN metadata TEXT;


-- Design Lookup Tables
CREATE TABLE lkp_design_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_design_status (id, name, description) VALUES (1, 'Preliminary Desktop', NULL);
INSERT INTO lkp_design_status (id, name, description) VALUES (2, 'Desktop Analysis (Remote)', NULL);
INSERT INTO lkp_design_status (id, name, description) VALUES (3, 'Provisional', NULL);
INSERT INTO lkp_design_status (id, name, description) VALUES (4, 'In Review', NULL);
INSERT INTO lkp_design_status (id, name, description) VALUES (5, 'Final', NULL);

CREATE TABLE lkp_design_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_design_sources (id, name, description) VALUES (1, 'Previous Site Visit', NULL);
INSERT INTO lkp_design_sources (id, name, description) VALUES (2, 'Desktop Analysis (Remote)', NULL);
INSERT INTO lkp_design_sources (id, name, description) VALUES (3, 'Field Work', NULL);


CREATE TABLE lkp_structure_mimics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_structure_mimics (id, name, description) VALUES (1, 'Beaver Dam', 'Structure has been designed to mimic the form and function of a beaver dam');
INSERT INTO lkp_structure_mimics (id, name, description) VALUES (2, 'Wood Jam', 'Structure has been designed to mimic the form and function of a wood jam or piece of woody debris');
INSERT INTO lkp_structure_mimics (id, name, description) VALUES (3, 'Other', 'Structure does not mimic a beaver dam, wood jam, or woody debris');


CREATE TABLE lkp_zoi_stage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lkp_zoi_stage (id, name, description) VALUES (1, 'Baseflow', 'Extent is the expected influence during or in response to baseflow discharge');
INSERT INTO lkp_zoi_stage (id, name, description) VALUES (2, 'Typical Flood', 'Extent is the expected influence during or in response to a typical flood event (e.g., 5 year recurrence interval)');
INSERT INTO lkp_zoi_stage (id, name, description) VALUES (3, 'Large Flood', 'Extent the expected influence during or in response to a large flood event (e.g., 20 year recurrence interval)');
INSERT INTO lkp_zoi_stage (id, name, description) VALUES (4, 'Other', 'Extent is not related to flood event');

CREATE TABLE structure_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    mimics_id INTEGER REFERENCES lkp_structure_mimics(id) ON DELETE CASCADE,
    construction_description TEXT,
    function_description TEXT,
    typical_posts INTEGER,
    typical_length NUMERIC,
    typical_width NUMERIC,
    typical_height NUMERIC,
    metadata TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO structure_types (id, name, mimics_id) VALUES (1, 'BDA Large', 1);
INSERT INTO structure_types (id, name, mimics_id) VALUES (2, 'BDA Small', 1);
INSERT INTO structure_types (id, name, mimics_id) VALUES (3, 'BDA Postless', 1);
INSERT INTO structure_types (id, name, mimics_id) VALUES (4, 'PALS Mid-Channel', 2);
INSERT INTO structure_types (id, name, mimics_id) VALUES (5, 'PALS Bank Attached', 2);
INSERT INTO structure_types (id, name, mimics_id) VALUES (6, 'Wood Jam', 2);
INSERT INTO structure_types (id, name, mimics_id) VALUES (7, 'Other', 3);

CREATE TABLE zoi_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    created DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO zoi_types (id, name, description) VALUES (1, 'Increase Channel Complexity', 'Combination of structure types used to maximize hydraulic diversity. BDAs force upstream ponds at baseflow. PALS force areas of high and low flow velocity to alter patterns of erosion and deposition, promote sorting, large woody debris recruitment');
INSERT INTO zoi_types (id, name, description) VALUES (2, 'Accelerate Incision Recovery', 'Use bank-attached and channel- spanning PALS to force bank erosion and channel widening; as well as channel-spanning PALS to force channel bed aggradation');
INSERT INTO zoi_types (id, name, description) VALUES (3, 'Lateral Channel Migration', 'Use of log structures to enhance sediment erossion rates on outside and deposition rates on the inside of channel meanders');
INSERT INTO zoi_types (id, name, description) VALUES (4, 'Increase Floodplain Connectivity', 'Channel-spanning PALS and primary and secondary BDAs to force flow on to accessible floodplain surfaces. BDAs force connectivity during baseflow, PALS force overbank flows during high flow');
INSERT INTO zoi_types (id, name, description) VALUES (5, 'Facilitate Beaver Translocation', 'Use primary BDAs to create deep-water habitat for translocation; use secondary BDAs to support primary dams by reducing head drop and increased extent of ponded area for forage access and refuge from predation');
INSERT INTO zoi_types (id, name, description) VALUES (6, 'Other', 'Area of hydraulic feature creation (e.g., eddy, shear zone, hydraulic jet)');



-- Design Spatial Table Fields and Relationships
ALTER TABLE zoi ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE zoi ADD COLUMN type_id INTEGER REFERENCES zoi_types(id);
ALTER TABLE zoi ADD COLUMN stage_id INTEGER REFERENCES lkp_zoi_stage(id);
ALTER TABLE zoi ADD COLUMN description TEXT;
ALTER TABLE zoi ADD COLUMN created DATETIME;
ALTER TABLE zoi ADD COLUMN metadata TEXT;

ALTER TABLE complexes ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE complexes ADD COLUMN name TEXT;
ALTER TABLE complexes ADD COLUMN initial_condition TEXT;
ALTER TABLE complexes ADD COLUMN target_condition TEXT;
ALTER TABLE complexes ADD COLUMN description TEXT;
ALTER TABLE complexes ADD COLUMN created DATETIME;
ALTER TABLE complexes ADD COLUMN metadata TEXT;

ALTER TABLE structure_lines ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE structure_lines ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(id);
ALTER TABLE structure_lines ADD COLUMN name TEXT;
ALTER TABLE structure_lines ADD COLUMN description TEXT;
ALTER TABLE structure_lines ADD COLUMN created DATETIME;
ALTER TABLE structure_lines ADD COLUMN metadata TEXT;

ALTER TABLE structure_points ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE structure_points ADD COLUMN structure_type_id INTEGER REFERENCES structure_types(id);
ALTER TABLE structure_points ADD COLUMN name TEXT;
ALTER TABLE structure_points ADD COLUMN description TEXT;
ALTER TABLE structure_points ADD COLUMN created DATETIME;
ALTER TABLE structure_points ADD COLUMN metadata TEXT;

-- pour points and catchments
ALTER TABLE pour_points ADD COLUMN name TEXT;
ALTER TABLE pour_points ADD COLUMN description TEXT;
ALTER TABLE pour_points ADD COLUMN latitude FLOAT;
ALTER TABLE pour_points ADD COLUMN longitude FLOAT;
ALTER TABLE pour_points ADD COLUMN basin_characteristics TEXT;
ALTER TABLE pour_points ADD COLUMN flow_statistics TEXT;
ALTER TABLE pour_points ADD COLUMN metadata TEXT;

ALTER TABLE catchments ADD COLUMN pour_point_id INT REFERENCES pour_points(fid) ON DELETE CASCADE;
ALTER TABLE catchments ADD COLUMN metadata TEXT;

-- stream gages
ALTER TABLE stream_gages ADD COLUMN site_code TEXT;
ALTER TABLE stream_gages ADD COLUMN site_name TEXT;
ALTER TABLE stream_gages ADD COLUMN site_type TEXT;
ALTER TABLE stream_gages ADD COLUMN site_datum TEXT;
ALTER TABLE stream_gages ADD COLUMN huc TEXT;
ALTER TABLE stream_gages ADD COLUMN agency TEXT;
ALTER TABLE stream_gages ADD COLUMN metadata TEXT;
ALTER TABLE stream_gages ADD COLUMN latitude REAL;
ALTER TABLE stream_gages ADD COLUMN longitude REAL;
CREATE UNIQUE INDEX ux_stream_gages_site_code ON stream_gages(site_code);
CREATE INDEX ix_stream_gages_site_name ON stream_gages(site_name);
CREATE INDEX ix_stream_gages_huc_cd ON stream_gages(huc);

-- stream gage discharge
CREATE TABLE stream_gage_discharges
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_gage_id INTEGER REFERENCES stream_gages(fid) ON DELETE CASCADE,
    measurement_date DATETIME,
    discharge REAL,
    discharge_code TEXT,
    gage_height REAL,
    gage_height_code TEXT,
    metadata TEXT,

    UNIQUE (stream_gage_id, measurement_date)
);
CREATE INDEX fx_stream_gage_discharges ON stream_gage_discharges(stream_gage_id);
-- CREATE INDEX ux_stream_gage_discharges ON stream_gage_discharges(stream_gage_id, measurement_date);

-- Profiles
CREATE TABLE profiles
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    profile_type_id INTEGER NOT NULL,-- REFERENCES lkp_mask_types(id),
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- profile features refer to the profile that they belong to
ALTER TABLE profile_features ADD COLUMN profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE profile_features ADD COLUMN display_label TEXT;
ALTER TABLE profile_features ADD COLUMN description TEXT;
ALTER TABLE profile_features ADD COLUMN metadata TEXT;

-- centerlines are generated from the centerline tool
ALTER TABLE profile_centerlines ADD COLUMN profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE profile_centerlines ADD COLUMN display_label TEXT;
ALTER TABLE profile_centerlines ADD COLUMN description TEXT;
ALTER TABLE profile_centerlines ADD COLUMN metadata TEXT;

-- Cross Sections
CREATE TABLE cross_sections
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    metadata TEXT,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- profile features refer to the profile that they belong to
ALTER TABLE cross_section_features ADD COLUMN cross_section_id INTEGER REFERENCES cross_sections(id) ON DELETE CASCADE;
ALTER TABLE cross_section_features ADD COLUMN sequence INTEGER;
ALTER TABLE cross_section_features ADD COLUMN distance REAL;
ALTER TABLE cross_section_features ADD COLUMN display_label TEXT;
ALTER TABLE cross_section_features ADD COLUMN description TEXT;
ALTER TABLE cross_section_features ADD COLUMN metadata TEXT;

-- add to geopackage contents
-- this is only necessary for non-spatial tables created using ddl.
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('analyses', 'attributes', 'analyses', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('analysis_metrics', 'attributes', 'analysis_metrics', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('protocols', 'attributes', 'protocols', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('protocol_methods', 'attributes', 'protocol_methods', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('methods', 'attributes', 'methods', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('method_layers', 'attributes', 'method_layers', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('layers', 'attributes', 'layers', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('context_layers', 'attributes', 'context_layers', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('protocol_layers', 'attributes', 'protocol_layers', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('projects', 'attributes', 'projects', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('events', 'attributes', 'events', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('event_layers', 'attributes', 'event_layers', 0);
-- INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('event_methods', 'attributes', 'event_methods', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('event_rasters', 'attributes', 'event_rasters', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('masks', 'attributes', 'masks', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('calculations', 'attributes', 'calculations', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('metrics', 'attributes', 'metrics', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('metric_levels', 'attributes', 'metric_levels', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('metric_values', 'attributes', 'metric_values', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('scratch_vectors', 'attributes', 'scratch_vectors', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('stream_gage_discharges', 'attributes', 'stream_gage_discharges', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('rasters', 'attributes', 'rasters', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('migrations', 'attributes', 'migrations', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('profiles', 'attributes', 'profiles', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('cross_sections', 'attributes', 'cross_sections', 0);

-- LOOKUP TABLES
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_metric_sources', 'attributes', 'lkp_metric_sources', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_platform', 'attributes', 'lkp_platform', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_representation', 'attributes', 'lkp_representation', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_mask_types', 'attributes', 'lkp_mask_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_structure_source', 'attributes', 'lkp_structure_source', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_dam_integrity', 'attributes', 'lkp_dam_integrity', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_beaver_maintenance', 'attributes', 'lkp_beaver_maintenance', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_thalweg_types', 'attributes', 'lkp_thalweg_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_active_extent_types', 'attributes', 'lkp_active_extent_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_junction_types', 'attributes', 'lkp_junction_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_geomorphic_unit_types', 'attributes', 'lkp_geomorphic_unit_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_vegetation_extent_types', 'attributes', 'lkp_vegetation_extent_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_cem_phase_types', 'attributes', 'lkp_cem_phase_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_floodplain_accessibility_types', 'attributes', 'lkp_floodplain_accessibility_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_vegetation_types', 'attributes', 'lkp_brat_vegetation_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_context_layer_types', 'attributes', 'lkp_context_layer_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_inundation_extent_types', 'attributes', 'lkp_inundation_extent_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_primary_channel', 'attributes', 'lkp_primary_channel', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_primary_unit', 'attributes', 'lkp_primary_unit', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_structure_forced', 'attributes', 'lkp_structure_forced', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_channel_unit_types', 'attributes', 'lkp_channel_unit_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_raster_types', 'attributes', 'lkp_raster_types', 0);

-- DESIGN TABLES
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_structure_mimics', 'attributes', 'lkp_structure_mimics', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_zoi_stage', 'attributes', 'lkp_zoi_stage', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_design_status', 'attributes', 'lkp_design_status', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('structure_types', 'attributes', 'structure_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('zoi_types', 'attributes', 'zoi_types', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_design_sources', 'attributes', 'lkp_design_sources', 0);

-- BRAT CIS TABLES
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_base_streampower', 'attributes', 'lkp_brat_base_streampower', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_high_streampower', 'attributes', 'lkp_brat_high_streampower', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_slope', 'attributes', 'lkp_brat_slope', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_dam_density', 'attributes', 'lkp_brat_dam_density', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_vegetation_cis', 'attributes', 'lkp_brat_vegetation_cis', 0);
INSERT INTO gpkg_contents (table_name, data_type, identifier, srs_id) VALUES ('lkp_brat_combined_cis', 'attributes', 'lkp_brat_combined_cis', 0);

