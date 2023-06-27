INSERT INTO layers (id, fc_name, display_name, geom_type, is_lookup, qml, description) VALUES (26, 'brat_cis_reaches', 'BRAT CIS Reaches', 'Linestring', 0, 'brat_cis_reaches.qml', NULL);
INSERT INTO method_layers (method_id, layer_id) VALUES (4, 26);

-- Alter the Brat CIS Reaches feature class
ALTER TABLE brat_cis_reaches ADD COLUMN event_id INTEGER REFERENCES events(id) ON DELETE CASCADE;
ALTER TABLE brat_cis_reaches ADD COLUMN observer_name TEXT;
ALTER TABLE brat_cis_reaches ADD COLUMN reach_id TEXT;
ALTER TABLE brat_cis_reaches ADD COLUMN observation_date DATE;
ALTER TABLE brat_cis_reaches ADD COLUMN reach_length FLOAT;
ALTER TABLE brat_cis_reaches ADD COLUMN notes TEXT;

ALTER TABLE brat_cis_reaches ADD COLUMN streamside_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
ALTER TABLE brat_cis_reaches ADD COLUMN riparian_veg_id INT REFERENCES lkp_brat_vegetation_types(id);
ALTER TABLE brat_cis_reaches ADD COLUMN veg_density_id INT REFERENCES lkp_brat_dam_density(id);

ALTER TABLE brat_cis_reaches ADD COLUMN base_streampower_id INT REFERENCES lkp_brat_base_streampower(id);
ALTER TABLE brat_cis_reaches ADD COLUMN high_streampower_id INT REFERENCES lkp_brat_high_streampower(id);

ALTER TABLE brat_cis_reaches ADD COLUMN slope_id INT REFERENCES lkp_brat_slope(id);

ALTER TABLE brat_cis_reaches ADD COLUMN combined_density_id INT REFERENCES lkp_brat_dam_density(id);