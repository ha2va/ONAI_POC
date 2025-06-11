from flask import Blueprint, render_template, request, redirect, url_for
from database import query_db, execute_db

bp = Blueprint('carriers', __name__, url_prefix='/carriers')


@bp.route('/list')
def list_carriers():
    query = "SELECT * FROM Carrier WHERE 1=1"
    params = []
    if request.args.get('carrier_name'):
        query += " AND carrier_name LIKE ?"
        params.append('%' + request.args['carrier_name'] + '%')
    if request.args.get('type'):
        query += " AND type LIKE ?"
        params.append('%' + request.args['type'] + '%')
    rows = query_db(query, params)
    return render_template('carriers.html', rows=rows)


@bp.route('/new', methods=['GET', 'POST'])
def new_carrier():
    if request.method == 'POST':
        execute_db(
            "INSERT INTO Carrier (carrier_name,type,reliability,supports_freezing,supports_dangerous_goods) VALUES (?,?,?,?,?)",
            [
                request.form['carrier_name'],
                request.form['type'],
                request.form.get('reliability'),
                1 if request.form.get('supports_freezing') else 0,
                1 if request.form.get('supports_dangerous_goods') else 0,
            ],
        )
        return redirect(url_for('carriers.list_carriers'))
    return render_template('carrier_form.html', carrier=None)


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_carrier(id):
    car = query_db("SELECT * FROM Carrier WHERE id=?", [id], one=True)
    if request.method == 'POST':
        execute_db(
            "UPDATE Carrier SET carrier_name=?, type=?, reliability=?, supports_freezing=?, supports_dangerous_goods=? WHERE id=?",
            [
                request.form['carrier_name'],
                request.form['type'],
                request.form.get('reliability'),
                1 if request.form.get('supports_freezing') else 0,
                1 if request.form.get('supports_dangerous_goods') else 0,
                id,
            ],
        )
        return redirect(url_for('carriers.list_carriers'))
    return render_template('carrier_form.html', carrier=car)


@bp.route('/delete/<int:id>', methods=['POST'])
def delete_carrier(id):
    execute_db("DELETE FROM Carrier WHERE id=?", [id])
    return redirect(url_for('carriers.list_carriers'))
