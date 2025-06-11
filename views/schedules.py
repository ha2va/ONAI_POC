from flask import Blueprint, render_template, request, redirect, url_for
from database import query_db, execute_db

bp = Blueprint('schedules', __name__, url_prefix='/schedules')


@bp.route('/list')
def list_schedules():
    base_query = "SELECT s.*, o.name as origin_name, d.name as destination_name FROM Schedule s LEFT JOIN Route r ON s.route_id=r.id LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id WHERE 1=1"
    params = []
    if request.args.get('route_id'):
        base_query += " AND s.route_id=?"
        params.append(request.args['route_id'])
    rows = query_db(base_query, params)
    routes = query_db("SELECT r.id, o.name as origin_name, d.name as destination_name FROM Route r LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id")
    return render_template('schedules.html', rows=rows, routes=routes)


@bp.route('/new', methods=['GET', 'POST'])
def new_schedule():
    routes = query_db("SELECT r.id, o.name as origin_name, d.name as destination_name FROM Route r LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id")
    if request.method == 'POST':
        execute_db(
            "INSERT INTO Schedule (route_id,departure_day,cutoff_day_offset,cutoff_hour,frequency,type) VALUES (?,?,?,?,?,?)",
            [
                request.form['route_id'],
                request.form['departure_day'],
                request.form.get('cutoff_day_offset'),
                request.form.get('cutoff_hour'),
                request.form.get('frequency'),
                request.form['type'],
            ],
        )
        return redirect(url_for('schedules.list_schedules'))
    return render_template('schedule_form.html', schedule=None, routes=routes)


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_schedule(id):
    schedule = query_db("SELECT * FROM Schedule WHERE id=?", [id], one=True)
    routes = query_db("SELECT r.id, o.name as origin_name, d.name as destination_name FROM Route r LEFT JOIN Location o ON r.origin_id=o.id LEFT JOIN Location d ON r.destination_id=d.id")
    if request.method == 'POST':
        execute_db(
            "UPDATE Schedule SET route_id=?, departure_day=?, cutoff_day_offset=?, cutoff_hour=?, frequency=?, type=? WHERE id=?",
            [
                request.form['route_id'],
                request.form['departure_day'],
                request.form.get('cutoff_day_offset'),
                request.form.get('cutoff_hour'),
                request.form.get('frequency'),
                request.form['type'],
                id,
            ],
        )
        return redirect(url_for('schedules.list_schedules'))
    return render_template('schedule_form.html', schedule=schedule, routes=routes)


@bp.route('/delete/<int:id>', methods=['POST'])
def delete_schedule(id):
    execute_db("DELETE FROM Schedule WHERE id=?", [id])
    return redirect(url_for('schedules.list_schedules'))
