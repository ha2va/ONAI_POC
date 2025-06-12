from flask import Blueprint, render_template, request
from database import query_db
from plan_utils import recommend_plans

bp = Blueprint('plan', __name__, url_prefix='')


@bp.route('/plan', methods=['GET', 'POST'])
def plan():
    locations = query_db("SELECT id, name, type FROM Location")
    types = sorted({l['type'] for l in locations})
    origin_type = dest_type = origin_id = dest_id = start_date = end_date = None
    weight = requires_freezing = is_dangerous = None
    plans = applied_policies = None
    if request.method == 'POST':
        origin_type = request.form.get('origin_type')
        dest_type = request.form.get('dest_type')
        origin_id = int(request.form.get('origin_id'))
        dest_id = int(request.form.get('dest_id'))
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        weight = float(request.form.get('weight') or 0)
        requires_freezing = 1 if request.form.get('requires_freezing') else 0
        is_dangerous = 1 if request.form.get('is_dangerous') else 0
        shipment = {
            'weight': weight,
            'requires_freezing': requires_freezing,
            'is_dangerous': is_dangerous,
        }
        plans, applied_policies = recommend_plans(origin_id, dest_id, start_date, end_date, shipment)
    return render_template(
        'plan.html',
        types=types,
        locations=locations,
        origin_type=origin_type,
        dest_type=dest_type,
        origin_id=origin_id,
        dest_id=dest_id,
        start_date=start_date,
        end_date=end_date,
        weight=weight,
        requires_freezing=requires_freezing,
        is_dangerous=is_dangerous,
        plans=plans,
        applied_policies=applied_policies,
    )
