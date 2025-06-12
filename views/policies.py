from flask import Blueprint, render_template, request, redirect, url_for
from database import query_db, execute_db
import json

bp = Blueprint('policies', __name__, url_prefix='/policies')

@bp.route('/')
def list_policies():
    rows = query_db("SELECT * FROM Policy")
    return render_template('policies.html', rows=rows)

@bp.route('/new', methods=['GET', 'POST'])
def new_policy():
    if request.method == 'POST':
        execute_db(
            "INSERT INTO Policy (description, conditions, action, active) VALUES (?,?,?,?)",
            [
                request.form.get('description'),
                request.form.get('conditions_json'),
                request.form.get('action_json'),
                1 if request.form.get('active') else 0,
            ],
        )
        return redirect(url_for('policies.list_policies'))
    return render_template('policy_form.html', policy=None)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_policy(id):
    pol = query_db("SELECT * FROM Policy WHERE id=?", [id], one=True)
    if request.method == 'POST':
        execute_db(
            "UPDATE Policy SET description=?, conditions=?, action=?, active=? WHERE id=?",
            [
                request.form.get('description'),
                request.form.get('conditions_json'),
                request.form.get('action_json'),
                1 if request.form.get('active') else 0,
                id,
            ],
        )
        return redirect(url_for('policies.list_policies'))
    return render_template('policy_form.html', policy=pol)

@bp.route('/delete/<int:id>', methods=['POST'])
def delete_policy(id):
    execute_db("DELETE FROM Policy WHERE id=?", [id])
    return redirect(url_for('policies.list_policies'))
