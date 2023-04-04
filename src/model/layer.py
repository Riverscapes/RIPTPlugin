import sqlite3
from .db_item import DBItem


class Layer(DBItem):
    """Represents the definition of a layer that can be used by an event protocol.

    This class possesses the properties needed to add the layer to the map (with the addition of
    the event id definition query filter."""

    def __init__(self, id: int, fc_name: str, display_name: str, qml: str, is_lookup: bool, geom_type: str, description: str):
        # Must use the display name as the official db_item name so that it is the string displayed in UI
        super().__init__('layers', id, display_name)
        self.fc_name = fc_name
        self.qml = qml
        self.is_lookup = is_lookup
        self.geom_type = geom_type
        self.description = description
        self.icon = 'layer'


def load_layers(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM layers')
    return {row['id']: Layer(
        row['id'],
        row['fc_name'],
        row['display_name'],
        row['qml'],
        row['is_lookup'] != 0,
        row['geom_type'],
        row['description']
    ) for row in curs.fetchall()}


def load_non_method_layers(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT l.*FROM layers l LEFT JOIN method_layers m on l.id = m.layer_id WHERE m.method_id IS NULL AND l.is_lookup = 0')
    return {row['id']: Layer(
        row['id'],
        row['fc_name'],
        row['display_name'],
        row['qml'],
        row['is_lookup'] != 0,
        row['geom_type'],
        row['description']
    ) for row in curs.fetchall()}
