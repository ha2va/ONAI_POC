from flask import Blueprint, jsonify
from database import query_all, query_db

bp = Blueprint('api', __name__)

@bp.route('/carriers')
def get_carriers():
    return jsonify(query_all('Carrier'))

@bp.route('/locations')
def get_locations():
    return jsonify(query_all('Location'))

@bp.route('/routes')
def get_routes():
    return jsonify(query_all('Route'))

@bp.route('/schedules')
def get_schedules():
    return jsonify(query_all('Schedule'))

@bp.route('/shipments')
def get_shipments():
    return jsonify(query_all('Shipment'))

@bp.route('/costitems')
def get_costitems():
    return jsonify(query_all('CostItem'))

@bp.route('/locationcoverage')
def get_location_coverage():
    return jsonify(query_all('LocationCoverage'))

@bp.route('/tariffs')
def get_tariffs():
    return jsonify(query_all('Tariff'))

@bp.route('/tariff/<int:id>')
def get_tariff(id):
    row = query_db("SELECT * FROM Tariff WHERE id=?", [id], one=True)
    return jsonify(dict(row) if row else {})
