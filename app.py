from flask import Flask, g, jsonify, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
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
'''

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


def find_plans(origin_id, dest_id):
    routes = query_db(
        "SELECT r.id, r.origin_id, o.name as origin_name, r.destination_id, d.name as destination_name, r.base_cost, r.lead_time "
        "FROM Route r "
        "LEFT JOIN Location o ON r.origin_id=o.id "
        "LEFT JOIN Location d ON r.destination_id=d.id"
    )
    adj = {}
    for r in routes:
        adj.setdefault(r['origin_id'], []).append(r)

    plans = []

    def dfs(current, path, visited):
        if current == dest_id:
            plans.append(list(path))
            return
        for r in adj.get(current, []):
            if r['destination_id'] not in visited:
                visited.add(r['destination_id'])
                path.append(r)
                dfs(r['destination_id'], path, visited)
                path.pop()
                visited.remove(r['destination_id'])

    dfs(origin_id, [], {origin_id})
    result = []
    for plan_routes in plans:
        total_cost = sum(r['base_cost'] or 0 for r in plan_routes)
        total_lead = sum(r['lead_time'] or 0 for r in plan_routes)
        result.append({'routes': plan_routes, 'total_cost': total_cost, 'total_lead_time': total_lead})
    return result



# Web UI routes
@app.route('/')
def index():
    return redirect(url_for('list_locations'))

@app.route('/locations/list')
def list_locations():
    query = "SELECT * FROM Location WHERE 1=1"
    params = []
    if request.args.get('name'):
        query += " AND name LIKE ?"
        params.append('%'+request.args['name']+'%')
    if request.args.get('type'):
        query += " AND type LIKE ?"
        params.append('%'+request.args['type']+'%')
    if request.args.get('country'):
        query += " AND country LIKE ?"
        params.append('%'+request.args['country']+'%')
    rows = query_db(query, params)
    return render_template('locations.html', rows=rows)

@app.route('/locations/new', methods=['GET','POST'])
def new_location():
    if request.method=='POST':
        execute_db("INSERT INTO Location (name,type,country,supports_freezing,supports_storage,supports_dangerous_goods) VALUES (?,?,?,?,?,?)",
                   [request.form['name'], request.form['type'], request.form['country'],
                    1 if request.form.get('supports_freezing') else 0,
                    1 if request.form.get('supports_storage') else 0,
                    1 if request.form.get('supports_dangerous_goods') else 0])
        return redirect(url_for('list_locations'))
    return render_template('location_form.html', location=None)

@app.route('/locations/edit/<int:id>', methods=['GET','POST'])
def edit_location(id):
    loc = query_db("SELECT * FROM Location WHERE id=?", [id], one=True)
    if request.method=='POST':
        execute_db("UPDATE Location SET name=?, type=?, country=?, supports_freezing=?, supports_storage=?, supports_dangerous_goods=? WHERE id=?",
                   [request.form['name'], request.form['type'], request.form['country'],
                    1 if request.form.get('supports_freezing') else 0,
                    1 if request.form.get('supports_storage') else 0,
                    1 if request.form.get('supports_dangerous_goods') else 0, id])
        return redirect(url_for('list_locations'))
    return render_template('location_form.html', location=loc)

@app.route('/locations/delete/<int:id>', methods=['POST'])
def delete_location(id):
    execute_db("DELETE FROM Location WHERE id=?", [id])
    return redirect(url_for('list_locations'))

@app.route('/carriers/list')
def list_carriers():
    query = "SELECT * FROM Carrier WHERE 1=1"
    params = []
    if request.args.get('carrier_name'):
        query += " AND carrier_name LIKE ?"
        params.append('%'+request.args['carrier_name']+'%')
    if request.args.get('type'):
        query += " AND type LIKE ?"
        params.append('%'+request.args['type']+'%')
    rows = query_db(query, params)
    return render_template('carriers.html', rows=rows)

@app.route('/carriers/new', methods=['GET','POST'])
def new_carrier():
    if request.method=='POST':
        execute_db("INSERT INTO Carrier (carrier_name,type,reliability,supports_freezing,supports_dangerous_goods) VALUES (?,?,?,?,?)",
                   [request.form['carrier_name'], request.form['type'], request.form.get('reliability'),
                    1 if request.form.get('supports_freezing') else 0,
                    1 if request.form.get('supports_dangerous_goods') else 0])
        return redirect(url_for('list_carriers'))
    return render_template('carrier_form.html', carrier=None)

@app.route('/carriers/edit/<int:id>', methods=['GET','POST'])
def edit_carrier(id):
    car = query_db("SELECT * FROM Carrier WHERE id=?", [id], one=True)
    if request.method=='POST':
        execute_db("UPDATE Carrier SET carrier_name=?, type=?, reliability=?, supports_freezing=?, supports_dangerous_goods=? WHERE id=?",
                   [request.form['carrier_name'], request.form['type'], request.form.get('reliability'),
                    1 if request.form.get('supports_freezing') else 0,
                    1 if request.form.get('supports_dangerous_goods') else 0, id])
        return redirect(url_for('list_carriers'))
    return render_template('carrier_form.html', carrier=car)

@app.route('/carriers/delete/<int:id>', methods=['POST'])
def delete_carrier(id):
    execute_db("DELETE FROM Carrier WHERE id=?", [id])
    return redirect(url_for('list_carriers'))

@app.route('/routes/list')
def list_routes():
    query = (
        "SELECT r.*, o.name as origin_name, d.name as destination_name, c.carrier_name "
        "FROM Route r "
        "LEFT JOIN Location o ON r.origin_id=o.id "
        "LEFT JOIN Location d ON r.destination_id=d.id "
        "LEFT JOIN Carrier c ON r.carrier_id=c.id WHERE 1=1"
    )
    params = []
    if request.args.get('origin'):
        query += " AND o.name LIKE ?"
        params.append('%' + request.args['origin'] + '%')
    if request.args.get('destination'):
        query += " AND d.name LIKE ?"
        params.append('%' + request.args['destination'] + '%')
    type_filter = request.args.get('type')
    if type_filter and type_filter != 'ALL':
        query += " AND r.type = ?"
        params.append(type_filter)
    rows = query_db(query, params)
    types = query_db("SELECT DISTINCT type FROM Route")
    return render_template('routes.html', rows=rows, types=types)

@app.route('/routes/new', methods=['GET','POST'])
def new_route():
    locations = query_db("SELECT id, name FROM Location")
    carriers = query_db("SELECT id, carrier_name FROM Carrier")
    if request.method=='POST':
        execute_db("INSERT INTO Route (origin_id,destination_id,carrier_id,base_cost,lead_time,transport_mode,type,supports_freezing,supports_dangerous_goods) VALUES (?,?,?,?,?,?,?,?,?)",
                   [request.form['origin_id'], request.form['destination_id'], request.form['carrier_id'], request.form.get('base_cost'), request.form.get('lead_time'), request.form['transport_mode'], request.form['type'], 1 if request.form.get('supports_freezing') else 0, 1 if request.form.get('supports_dangerous_goods') else 0])
        return redirect(url_for('list_routes'))
    return render_template('route_form.html', route=None, locations=locations, carriers=carriers)

@app.route('/routes/edit/<int:id>', methods=['GET','POST'])
def edit_route(id):
    route = query_db("SELECT * FROM Route WHERE id=?", [id], one=True)
    locations = query_db("SELECT id, name FROM Location")
    carriers = query_db("SELECT id, carrier_name FROM Carrier")
    if request.method=='POST':
        execute_db("UPDATE Route SET origin_id=?, destination_id=?, carrier_id=?, base_cost=?, lead_time=?, transport_mode=?, type=?, supports_freezing=?, supports_dangerous_goods=? WHERE id=?",
                   [request.form['origin_id'], request.form['destination_id'], request.form['carrier_id'], request.form.get('base_cost'), request.form.get('lead_time'), request.form['transport_mode'], request.form['type'], 1 if request.form.get('supports_freezing') else 0, 1 if request.form.get('supports_dangerous_goods') else 0, id])
        return redirect(url_for('list_routes'))
    return render_template('route_form.html', route=route, locations=locations, carriers=carriers)

@app.route('/routes/delete/<int:id>', methods=['POST'])
def delete_route(id):
    execute_db("DELETE FROM Route WHERE id=?", [id])
    return redirect(url_for('list_routes'))

@app.route('/schedules/list')
def list_schedules():
    base_query = "SELECT s.*, o.name as origin_name, d.name as destination_name FROM Schedule s LEFT JOIN Route r ON s.route_id=r.id LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id WHERE 1=1"
    params = []
    if request.args.get('route_id'):
        base_query += " AND s.route_id=?"
        params.append(request.args['route_id'])
    rows = query_db(base_query, params)
    routes = query_db("SELECT r.id, o.name as origin_name, d.name as destination_name FROM Route r LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id")
    return render_template('schedules.html', rows=rows, routes=routes)

@app.route('/schedules/new', methods=['GET','POST'])
def new_schedule():
    routes = query_db("SELECT r.id, o.name as origin_name, d.name as destination_name FROM Route r LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id")
    if request.method=='POST':
        execute_db("INSERT INTO Schedule (route_id,departure_day,cutoff_day_offset,cutoff_hour,frequency,type) VALUES (?,?,?,?,?,?)",
                   [request.form['route_id'], request.form['departure_day'], request.form.get('cutoff_day_offset'), request.form.get('cutoff_hour'), request.form.get('frequency'), request.form['type']])
        return redirect(url_for('list_schedules'))
    return render_template('schedule_form.html', schedule=None, routes=routes)

@app.route('/schedules/edit/<int:id>', methods=['GET','POST'])
def edit_schedule(id):
    schedule = query_db("SELECT * FROM Schedule WHERE id=?", [id], one=True)
    routes = query_db("SELECT r.id, o.name as origin_name, d.name as destination_name FROM Route r LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id")
    if request.method=='POST':
        execute_db("UPDATE Schedule SET route_id=?, departure_day=?, cutoff_day_offset=?, cutoff_hour=?, frequency=?, type=? WHERE id=?",
                   [request.form['route_id'], request.form['departure_day'], request.form.get('cutoff_day_offset'), request.form.get('cutoff_hour'), request.form.get('frequency'), request.form['type'], id])
        return redirect(url_for('list_schedules'))
    return render_template('schedule_form.html', schedule=schedule, routes=routes)

@app.route('/schedules/delete/<int:id>', methods=['POST'])
def delete_schedule(id):
    execute_db("DELETE FROM Schedule WHERE id=?", [id])
    return redirect(url_for('list_schedules'))


@app.route('/plan', methods=['GET', 'POST'])
def plan():
    locations = query_db("SELECT id, name, type FROM Location")
    types = sorted({l['type'] for l in locations})
    origin_type = dest_type = origin_id = dest_id = None
    plans = None
    if request.method == 'POST':
        origin_type = request.form.get('origin_type')
        dest_type = request.form.get('dest_type')
        origin_id = int(request.form.get('origin_id'))
        dest_id = int(request.form.get('dest_id'))
        plans = find_plans(origin_id, dest_id)
    return render_template('plan.html', types=types, locations=locations,
                           origin_type=origin_type, dest_type=dest_type,
                           origin_id=origin_id, dest_id=dest_id, plans=plans)

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

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
