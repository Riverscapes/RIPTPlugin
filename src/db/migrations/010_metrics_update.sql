-- Purge existing metrics
DELETE FROM analyses;
DELETE FROM metrics;

-- Add jam and dam density metrics
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (1, 1, 'Jam Density', 1, NULL, '{"layers": [{"layer_name": "structural_elements_points", "count_field": "Structure Count", "attribute_filter": {"field_name": "Type", "values": ["Jam", "Jam Complex"]}}, {"layer_name": "structural_elements_lines", "attribute_filter": {"field_name": "Type", "values": ["Jam", "Jam Complex"]}}, {"layer_name": "structural_elements_areas", "attribute_filter": {"field_name": "Type", "values": ["Jam", "Jam Complex"]}}], "normalization": "centerline"}', '{"min_value": 0}');
INSERT INTO metrics (id, calculation_id, name, default_level_id, unit_id, metric_params, metadata) VALUES (2, 1, 'Dam Density', 1, NULL, '{"layers": [{"layer_name": "structural_elements_points", "count_field": "Structure Count", "attribute_filter": {"field_name": "Type", "values": ["Dam", "Dam Complex"]}}, {"layer_name": "structural_elements_lines", "attribute_filter": {"field_name": "Type", "values": ["Dam", "Dam Complex"]}}, {"layer_name": "structural_elements_areas", "attribute_filter": {"field_name": "Type", "values": ["Dam", "Dam Complex"]}}], "normalization": "centerline"}', '{"min_value": 0}');