from flask import Blueprint, render_template, request, redirect, url_for
from database import query_db, execute_db

bp = Blueprint('routes', __name__, url_prefix='/routes')


@bp.route('/list')
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


@bp.route('/new', methods=['GET', 'POST'])
def new_route():
    locations = query_db("SELECT id, name FROM Location")
    carriers = query_db("SELECT id, carrier_name FROM Carrier")
    if request.method == 'POST':
        execute_db(
            "INSERT INTO Route (origin_id,destination_id,carrier_id,base_cost,lead_time,transport_mode,type,supports_freezing,supports_dangerous_goods) VALUES (?,?,?,?,?,?,?,?,?)",
            [
                request.form['origin_id'],
                request.form['destination_id'],
                request.form['carrier_id'],
                request.form.get('base_cost'),
                request.form.get('lead_time'),
                request.form['transport_mode'],
                request.form['type'],
                1 if request.form.get('supports_freezing') else 0,
                1 if request.form.get('supports_dangerous_goods') else 0,
            ],
        )
        return redirect(url_for('routes.list_routes'))
    return render_template('route_form.html', route=None, locations=locations, carriers=carriers)


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_route(id):
    route = query_db("SELECT * FROM Route WHERE id=?", [id], one=True)
    locations = query_db("SELECT id, name FROM Location")
    carriers = query_db("SELECT id, carrier_name FROM Carrier")
    if request.method == 'POST':
        execute_db(
            "UPDATE Route SET origin_id=?, destination_id=?, carrier_id=?, base_cost=?, lead_time=?, transport_mode=?, type=?, supports_freezing=?, supports_dangerous_goods=? WHERE id=?",
            [
                request.form['origin_id'],
                request.form['destination_id'],
                request.form['carrier_id'],
                request.form.get('base_cost'),
                request.form.get('lead_time'),
                request.form['transport_mode'],
                request.form['type'],
                1 if request.form.get('supports_freezing') else 0,
                1 if request.form.get('supports_dangerous_goods') else 0,
                id,
            ],
        )
        return redirect(url_for('routes.list_routes'))
    return render_template('route_form.html', route=route, locations=locations, carriers=carriers)


@bp.route('/delete/<int:id>', methods=['POST'])
def delete_route(id):
    execute_db("DELETE FROM Route WHERE id=?", [id])
    return redirect(url_for('routes.list_routes'))
