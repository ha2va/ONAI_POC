from flask import Blueprint, render_template, request, redirect, url_for
from database import query_db, execute_db
import json

bp = Blueprint('policies', __name__, url_prefix='/policies')

@bp.route('/')
def list_policies():
    rows = query_db("SELECT * FROM Policy ORDER BY priority ASC")
    return render_template('policies.html', rows=rows)

@bp.route('/new', methods=['GET', 'POST'])
def new_policy():
    if request.method == 'POST':
        max_p = query_db("SELECT MAX(priority) as m FROM Policy", one=True)['m'] or 0
        prio = request.form.get('priority')
        prio = int(prio) if prio not in (None, '') else int(max_p) + 1
        execute_db(
            "INSERT INTO Policy (description, conditions, action, active, priority) VALUES (?,?,?,?,?)",
            [
                request.form.get('description'),
                request.form.get('conditions_json'),
                request.form.get('action_json'),
                1 if request.form.get('active') else 0,
                prio,
            ],
        )
        return redirect(url_for('policies.list_policies'))
    return render_template('policy_form.html', policy=None)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_policy(id):
    pol = query_db("SELECT * FROM Policy WHERE id=?", [id], one=True)
    if request.method == 'POST':
        execute_db(
            "UPDATE Policy SET description=?, conditions=?, action=?, active=?, priority=? WHERE id=?",
            [
                request.form.get('description'),
                request.form.get('conditions_json'),
                request.form.get('action_json'),
                1 if request.form.get('active') else 0,
                int(request.form.get('priority') or 0),
                id,
            ],
        )
        return redirect(url_for('policies.list_policies'))
    return render_template('policy_form.html', policy=pol)

@bp.route('/delete/<int:id>', methods=['POST'])
def delete_policy(id):
    execute_db("DELETE FROM Policy WHERE id=?", [id])
    return redirect(url_for('policies.list_policies'))

@bp.route('/move/<int:id>/<string:direction>', methods=['POST'])
def move_policy(id, direction):
    pol = query_db("SELECT id, priority FROM Policy WHERE id=?", [id], one=True)
    if not pol:
        return redirect(url_for('policies.list_policies'))
    delta = -1 if direction == 'up' else 1
    new_pri = pol['priority'] + delta
    other = query_db("SELECT id FROM Policy WHERE priority=?", [new_pri], one=True)
    if other:
        execute_db("UPDATE Policy SET priority=? WHERE id=?", [pol['priority'], other['id']])
    execute_db("UPDATE Policy SET priority=? WHERE id=?", [new_pri, id])
    return redirect(url_for('policies.list_policies'))
