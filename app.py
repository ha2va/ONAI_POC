from flask import Flask, g, jsonify, render_template, request, redirect, url_for
import sqlite3
import json

app = Flask(__name__)
DATABASE = 'poc.db'

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
'''
POLICY_FILE = 'policies.json'

def load_policies():
    try:
        with open(POLICY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_policies(policies):
    with open(POLICY_FILE, 'w') as f:
        json.dump(policies, f, ensure_ascii=False, indent=2)

def check_condition(shipment, cond):
    field = cond.get('fact')
    op = cond.get('operator')
    value = cond.get('value')
    shipment_value = shipment.get(field)
    if isinstance(value, str):
        if value.lower() in ['true', 'on', '1']:
            value = True
        elif value.lower() in ['false', 'off', '0']:
            value = False
    if op == '=':
        return shipment_value == value
    if op == '>':
        return shipment_value is not None and float(shipment_value) > float(value)
    if op == '<':
        return shipment_value is not None and float(shipment_value) < float(value)
    return False

def filter_routes_by_policies(routes, shipment):
    policies = [p for p in load_policies() if p.get('active')]
    filtered = routes[:]
    summary = []
    for policy in policies:
        if all(check_condition(shipment, c) for c in policy.get('conditions', [])):
            action = policy.get('action', {})
            route_ids = action.get('route_ids', [])
            if action.get('type') == 'allow_only':
                filtered = [r for r in filtered if r['id'] in route_ids]
                summary.append(f"{policy['description']} 적용: 지정된 라우트만 허용")
            elif action.get('type') == 'deny':
                filtered = [r for r in filtered if r['id'] not in route_ids]
                summary.append(f"{policy['description']} 적용: 일부 라우트 제외")
    return filtered, '; '.join(summary)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
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

@app.route('/carriers')
def get_carriers():
    return jsonify(query_all('Carrier'))

@app.route('/locations')
def get_locations():
    return jsonify(query_all('Location'))

@app.route('/routes')
def get_routes():
    return jsonify(query_all('Route'))

@app.route('/schedules')
def get_schedules():
    return jsonify(query_all('Schedule'))

@app.route('/shipments')
def get_shipments():
    return jsonify(query_all('Shipment'))

@app.route('/costitems')
def get_costitems():
    return jsonify(query_all('CostItem'))

@app.route('/locationcoverage')
def get_location_coverage():
    return jsonify(query_all('LocationCoverage'))

# Policy management UI
@app.route('/policy', methods=['GET', 'POST'])
def policy_list():
    policies = load_policies()
    if request.method == 'POST':
        new_id = max([p['id'] for p in policies], default=0) + 1
        def parse_val(val):
            if val is None:
                return None
            if val.lower() in ['true', 'on', '1']:
                return True
            if val.lower() in ['false', 'off', '0']:
                return False
            try:
                return float(val)
            except ValueError:
                return val

        cond = {
            'fact': request.form.get('fact'),
            'operator': request.form.get('operator'),
            'value': parse_val(request.form.get('value'))
        }
        action = {
            'type': request.form.get('action_type'),
            'route_ids': [int(x) for x in request.form.get('route_ids', '').split(',') if x]
        }
        policies.append({
            'id': new_id,
            'description': request.form.get('description'),
            'conditions': [cond],
            'action': action,
            'active': bool(request.form.get('active'))
        })
        save_policies(policies)
        return redirect(url_for('policy_list'))
    return render_template('policy_list.html', policies=policies)

@app.route('/policy/<int:pid>/toggle', methods=['POST'])
def policy_toggle(pid):
    policies = load_policies()
    for p in policies:
        if p['id'] == pid:
            p['active'] = not p.get('active', True)
    save_policies(policies)
    return redirect(url_for('policy_list'))

@app.route('/policy/<int:pid>/delete', methods=['POST'])
def policy_delete(pid):
    policies = [p for p in load_policies() if p['id'] != pid]
    save_policies(policies)
    return redirect(url_for('policy_list'))

# Route recommendation applying policies
@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    routes = []
    summary = ''
    if request.method == 'POST':
        origin = request.form.get('origin_id')
        dest = request.form.get('destination_id')
        weight = float(request.form.get('weight') or 0)
        requires_freezing = bool(request.form.get('requires_freezing'))
        is_dangerous = bool(request.form.get('is_dangerous'))

        cur = get_db().execute(
            'SELECT * FROM Route WHERE origin_id=? AND destination_id=?',
            (origin, dest)
        )
        routes = [dict(row) for row in cur.fetchall()]
        cur.close()
        shipment = {
            'weight': weight,
            'requires_freezing': requires_freezing,
            'is_dangerous': is_dangerous
        }
        routes, summary = filter_routes_by_policies(routes, shipment)
    return render_template('recommend.html', routes=routes, summary=summary)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
