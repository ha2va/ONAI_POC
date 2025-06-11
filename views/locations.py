from flask import Blueprint, render_template, request, redirect, url_for
from database import query_db, execute_db

bp = Blueprint('locations', __name__, url_prefix='/locations')


@bp.route('/list')
def list_locations():
    query = "SELECT * FROM Location WHERE 1=1"
    params = []
    if request.args.get('name'):
        query += " AND name LIKE ?"
        params.append('%' + request.args['name'] + '%')
    if request.args.get('type'):
        query += " AND type LIKE ?"
        params.append('%' + request.args['type'] + '%')
    if request.args.get('country'):
        query += " AND country LIKE ?"
        params.append('%' + request.args['country'] + '%')
    rows = query_db(query, params)
    return render_template('locations.html', rows=rows)


@bp.route('/new', methods=['GET', 'POST'])
def new_location():
    if request.method == 'POST':
        execute_db(
            "INSERT INTO Location (name,type,country,supports_freezing,supports_storage,supports_dangerous_goods) VALUES (?,?,?,?,?,?)",
            [
                request.form['name'],
                request.form['type'],
                request.form['country'],
                1 if request.form.get('supports_freezing') else 0,
                1 if request.form.get('supports_storage') else 0,
                1 if request.form.get('supports_dangerous_goods') else 0,
            ],
        )
        return redirect(url_for('locations.list_locations'))
    return render_template('location_form.html', location=None)


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_location(id):
    loc = query_db("SELECT * FROM Location WHERE id=?", [id], one=True)
    if request.method == 'POST':
        execute_db(
            "UPDATE Location SET name=?, type=?, country=?, supports_freezing=?, supports_storage=?, supports_dangerous_goods=? WHERE id=?",
            [
                request.form['name'],
                request.form['type'],
                request.form['country'],
                1 if request.form.get('supports_freezing') else 0,
                1 if request.form.get('supports_storage') else 0,
                1 if request.form.get('supports_dangerous_goods') else 0,
                id,
            ],
        )
        return redirect(url_for('locations.list_locations'))
    return render_template('location_form.html', location=loc)


@bp.route('/delete/<int:id>', methods=['POST'])
def delete_location(id):
    execute_db("DELETE FROM Location WHERE id=?", [id])
    return redirect(url_for('locations.list_locations'))
