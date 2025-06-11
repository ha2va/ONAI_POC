from flask import Blueprint, render_template, request, redirect, url_for
from database import query_db, execute_db

bp = Blueprint('tariffs', __name__, url_prefix='/tariffs')


@bp.route('/list')
def list_tariffs():
    base_query = (
        "SELECT t.*, o.name as origin_name, d.name as destination_name "
        "FROM Tariff t "
        "LEFT JOIN Route r ON t.route_id=r.id "
        "LEFT JOIN Location o ON r.origin_id=o.id "
        "LEFT JOIN Location d ON r.destination_id=d.id WHERE 1=1"
    )
    params = []
    route_id = request.args.get('route_id') or request.args.get('route_select')
    if route_id:
        base_query += " AND t.route_id=?"
        params.append(route_id)
    if request.args.get('valid_from'):
        base_query += " AND t.valid_from >= ?"
        params.append(request.args['valid_from'])
    if request.args.get('valid_to'):
        base_query += " AND t.valid_to <= ?"
        params.append(request.args['valid_to'])
    rows = query_db(base_query, params)
    routes = query_db("SELECT r.id, o.name as origin_name, d.name as destination_name FROM Route r LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id")
    return render_template('tariffs.html', rows=rows, routes=routes)


@bp.route('/new', methods=['GET', 'POST'])
def new_tariff():
    routes = query_db("SELECT r.id, o.name as origin_name, d.name as destination_name FROM Route r LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id")
    if request.method == 'POST':
        execute_db(
            "INSERT INTO Tariff (route_id, valid_from, valid_to, cost) VALUES (?,?,?,?)",
            [
                request.form['route_id'],
                request.form['valid_from'],
                request.form['valid_to'],
                request.form.get('cost'),
            ],
        )
        return redirect(url_for('tariffs.list_tariffs'))
    return render_template('tariff_form.html', tariff=None, routes=routes)


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_tariff(id):
    tariff = query_db("SELECT * FROM Tariff WHERE id=?", [id], one=True)
    routes = query_db("SELECT r.id, o.name as origin_name, d.name as destination_name FROM Route r LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id")
    if request.method == 'POST':
        execute_db(
            "UPDATE Tariff SET route_id=?, valid_from=?, valid_to=?, cost=? WHERE id=?",
            [
                request.form['route_id'],
                request.form['valid_from'],
                request.form['valid_to'],
                request.form.get('cost'),
                id,
            ],
        )
        return redirect(url_for('tariffs.list_tariffs'))
    return render_template('tariff_form.html', tariff=tariff, routes=routes)


@bp.route('/delete/<int:id>', methods=['POST'])
def delete_tariff(id):
    execute_db("DELETE FROM Tariff WHERE id=?", [id])
    return redirect(url_for('tariffs.list_tariffs'))
