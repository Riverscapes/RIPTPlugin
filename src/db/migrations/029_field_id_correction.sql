-- Update the attribute keys in the dce_lines, dce_points, and dce_polygons tables to use the machine_code instead of the label

-- Assuming the metadata JSON structure in the layers table is something like:
-- {
--     "fields": [
--         {
--             "label": "Structure Source",
--             "machine_code": "structure_source"
--         },
--         {
--             "label": "Dam State",
--             "machine_code": "dam_state"
--         },
--         ...
--     ]
-- }

-- Step 1: Create temporary tables to store the updated metadata
CREATE TEMP TABLE temp_dce_lines AS
SELECT dce_lines.fid, dce_lines.geom, dce_lines.event_id, dce_lines.event_layer_id, dce_lines.metadata
FROM dce_lines
JOIN layers ON dce_lines.event_layer_id = layers.id;

CREATE TEMP TABLE temp_dce_points AS
SELECT dce_points.fid, dce_points.geom, dce_points.event_id, dce_points.event_layer_id, dce_points.metadata
FROM dce_points
JOIN layers ON dce_points.event_layer_id = layers.id;

CREATE TEMP TABLE temp_dce_polygons AS
SELECT dce_polygons.fid, dce_polygons.geom, dce_polygons.event_id, dce_polygons.event_layer_id, dce_polygons.metadata
FROM dce_polygons
JOIN layers ON dce_polygons.event_layer_id = layers.id;

-- Step 2: Update the metadata JSON using the machine_code from the fields JSON in the layers table
UPDATE temp_dce_lines
SET metadata = json_set(
    temp_dce_lines.metadata,
    '$.attributes',
    json_patch(
        (SELECT json_group_object(
            json_extract(value, '$.machine_code'),
            json_extract(temp_dce_lines.metadata, '$.attributes.' || json_extract(value, '$.label'))
        )
        FROM json_each(layers.metadata, '$.fields')),
        json_object('notes', json_extract(temp_dce_lines.metadata, '$.attributes.Notes'))
    )
)
FROM layers
WHERE temp_dce_lines.event_layer_id = layers.id;

UPDATE temp_dce_points
SET metadata = json_set(
    temp_dce_points.metadata,
    '$.attributes',
    json_patch(
        (SELECT json_group_object(
            json_extract(value, '$.machine_code'),
            json_extract(temp_dce_points.metadata, '$.attributes.' || json_extract(value, '$.label'))
        )
        FROM json_each(layers.metadata, '$.fields')),
        json_object('notes', json_extract(temp_dce_points.metadata, '$.attributes.Notes'))
    )
)
FROM layers
WHERE temp_dce_points.event_layer_id = layers.id;

UPDATE temp_dce_polygons
SET metadata = json_set(
    temp_dce_polygons.metadata,
    '$.attributes',
    json_patch(
        (SELECT json_group_object(
            json_extract(value, '$.machine_code'),
            json_extract(temp_dce_polygons.metadata, '$.attributes.' || json_extract(value, '$.label'))
        )
        FROM json_each(layers.metadata, '$.fields')),
        json_object('notes', json_extract(temp_dce_polygons.metadata, '$.attributes.Notes'))
    )
)
FROM layers
WHERE temp_dce_polygons.event_layer_id = layers.id;

-- Step 3: Verify the update
SELECT fid, geom, event_id, event_layer_id, metadata
FROM temp_dce_lines;

SELECT fid, geom, event_id, event_layer_id, metadata
FROM temp_dce_points;

SELECT fid, geom, event_id, event_layer_id, metadata
FROM temp_dce_polygons;

-- Step 4: Update the original tables with the corrected metadata
UPDATE dce_lines
SET metadata = temp_dce_lines.metadata
FROM temp_dce_lines
WHERE dce_lines.fid = temp_dce_lines.fid;

UPDATE dce_points
SET metadata = temp_dce_points.metadata
FROM temp_dce_points
WHERE dce_points.fid = temp_dce_points.fid;

UPDATE dce_polygons
SET metadata = temp_dce_polygons.metadata
FROM temp_dce_polygons
WHERE dce_polygons.fid = temp_dce_polygons.fid;

-- Step 5: Drop the temporary tables
DROP TABLE temp_dce_lines;
DROP TABLE temp_dce_points;
DROP TABLE temp_dce_polygons;