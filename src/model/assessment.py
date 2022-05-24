import sqlite3
from .db_item import DBItem, dict_factory

ASSESSMENT_MACHINE_CODE = 'Assessment'


class Assessment(DBItem):

    def __init__(self, id: int, name: str, description: str, methods: dict, basemaps: dict):
        super().__init__(id, name)
        self.description = description
        self.methods = methods or {}
        self.basemaps = basemaps or {}

    def update(self, curs: sqlite3.Cursor, name: str, description: str, methods: dict, basemaps: dict):

        curs.execute('UPDATE bases SET name = ?, description = ?', [name, description])

        unused_method_ids = []
        curs.execute('SELECT method_id FROM assessment_methods WHERE assessment_id = ?', self.id)
        for row in curs.fetchall():
            if row['id'] not in methods.keys():
                unused_method_ids.append((self.id, row['method_id']))

        if len(unused_method_ids) > 0:
            curs.executemany('DELETE FROM assessment_methods where assessment_id = ? and method_id = ?', unused_method_ids)

        curs.executemany('INSERT INTO assessment_methods(assessment_id, method_id) VALUES (?, ?) ON CONFLICT (assessment_id, method_id) DO NOTHING', [self.id, methods.keys()])

        unused_basemap_ids = []
        curs.execute('SELECT basemap_id FROM assessment_bases WHERE assessment_id = ?', self.id)
        for row in curs.fetchall():
            if row['id'] not in basemaps.keys():
                unused_basemap_ids.append((self.id, row['basemap_id']))

        if len(unused_method_ids) > 0:
            curs.executemany('DELETE FROM assessment_bases where assessment_id = ? and base_id = ?', unused_basemap_ids)

        curs.executemany('INSERT INTO assessment_bases (assessment_id, base_id) VALUES (?, ?) ON CONFLICT(assessment_id, base_id) DO NOTHING', [self.id, basemaps.keys()])

        self.name = name
        self.description = description
        self.methods = methods
        self.basemaps = basemaps

    def delete(self, db_path: str, layers: dict) -> None:

        conn = sqlite3.connect(db_path)
        curs = conn.cursor()
        curs.execute('DELETE FROM assessments WHERE fid = ?', [self.id])

        # Delete spatial features associated with this assessment
        [curs.execute('DELETE FROM {} WHERE assessment_id = ?'.format(layer.fc_name), [self.id]) for layer in layers.values()]


def load_assessments(curs: sqlite3.Cursor, methods: dict, basemaps: dict) -> dict:

    curs.execute('SELECT * FROM assessments')
    assessments = {row['fid']: Assessment(
        row['fid'],
        row['name'],
        row['description'],
        None,
        None
    ) for row in curs.fetchall()}

    for assessment_id, assessment in assessments.items():
        curs.execute('SELECT method_id FROM assessment_methods WHERE assessment_id = ?', assessment_id)
        for row in curs.fetchall():
            assessment.methods.append(methods[row['method_id']])

        curs.execute('SELECT base_id FROM assessment_bases WHERE assessment_id = ?', assessment_id)
        for row in curs.fetchall():
            assessment.basemaps.append(basemaps[row['base_id']])

    return assessments


def add_assessment(db_path: str, project_id: int, name: str, description: str, methods: list, basemaps: list) -> Assessment:

    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute('INSERT INTO assessments (name, description) VALUES (?, ?)', [name, description if len(description) > 1 else None])
    assessment_id = curs.lastrowid

    curs.executemany("""INSERT INTO assessment_methods (assessment_id, method_id)
                SELECT ?, fid FROM methods WHERE name = ?""", [(assessment_id, method.id) for method in methods])

    curs.executemany("""INSERT INTO assessment_bases (assessment_id, base_id)
                SELECT ?, fid FROM bases WHERE name = ?""", [(assessment_id, basemap.id) for basemap in basemaps])

    conn.commit()

    return Assessment(assessment_id, name, description, methods, basemaps)
