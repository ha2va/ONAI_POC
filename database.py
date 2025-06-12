import sqlite3
from flask import g

DATABASE = 'db/onai_route.db'

SCHEMA = '''
CREATE TABLE IF NOT EXISTS Carrier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrier_name TEXT,
    type TEXT,
    reliability REAL,
    supports_freezing BOOLEAN,
    supports_dangerous_goods BOOLEAN
);

CREATE TABLE IF NOT EXISTS Location (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    type TEXT,
    country TEXT,
    supports_freezing BOOLEAN,
    supports_storage BOOLEAN,
    supports_dangerous_goods BOOLEAN
);

CREATE TABLE IF NOT EXISTS Route (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_id INTEGER,
    destination_id INTEGER,
    carrier_id INTEGER,
    base_cost REAL,
    lead_time REAL,
    transport_mode TEXT,
    type TEXT,
    supports_freezing BOOLEAN,
    supports_dangerous_goods BOOLEAN,
    FOREIGN KEY (origin_id) REFERENCES Location(id),
    FOREIGN KEY (destination_id) REFERENCES Location(id),
    FOREIGN KEY (carrier_id) REFERENCES Carrier(id)
);

CREATE TABLE IF NOT EXISTS Schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER,
    departure_day TEXT,
    cutoff_day_offset INTEGER,
    cutoff_hour INTEGER,
    frequency INTEGER,
    type TEXT,
    FOREIGN KEY (route_id) REFERENCES Route(id)
);

CREATE TABLE IF NOT EXISTS Shipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_id INTEGER,
    destination_id INTEGER,
    weight REAL,
    deadline DATETIME,
    requires_freezing BOOLEAN,
    is_dangerous BOOLEAN,
    incoterms TEXT,
    type TEXT,
    FOREIGN KEY (origin_id) REFERENCES Location(id),
    FOREIGN KEY (destination_id) REFERENCES Location(id)
);

CREATE TABLE IF NOT EXISTS CostItem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    applies_to TEXT,
    applies_to_id INTEGER,
    cost_type TEXT,
    amount REAL,
    trigger_type TEXT,
    trigger_operator TEXT,
    trigger_value REAL,
    type TEXT
);

CREATE TABLE IF NOT EXISTS LocationCoverage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id INTEGER,
    covers_location_id INTEGER,
    FOREIGN KEY (warehouse_id) REFERENCES Location(id),
    FOREIGN KEY (covers_location_id) REFERENCES Location(id)
);

CREATE TABLE IF NOT EXISTS Tariff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER,
    valid_from DATE,
    valid_to DATE,
    cost REAL,
    FOREIGN KEY (route_id) REFERENCES Route(id)
);

CREATE TABLE IF NOT EXISTS Policy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    conditions TEXT,
    action TEXT,
    active BOOLEAN,
    priority INTEGER
);
'''

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()

def query_all(table):
    cur = get_db().execute(f'SELECT * FROM {table}')
    rows = cur.fetchall()
    cur.close()
    return [dict(row) for row in rows]

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (dict(rv[0]) if rv else None) if one else [dict(r) for r in rv]

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid
