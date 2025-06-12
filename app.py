from flask import Flask, redirect, url_for

from database import init_db, close_connection
from views import (
    locations_bp,
    carriers_bp,
    routes_bp,
    schedules_bp,
    tariffs_bp,
    plan_bp,
    api_bp,
    policies_bp,
)

app = Flask(__name__)
app.teardown_appcontext(close_connection)

# 인덱스 페이지는 Locations 목록으로 리다이렉트
@app.route('/')
def index():
    return redirect(url_for('locations.list_locations'))

# 블루프린트 등록
app.register_blueprint(locations_bp)
app.register_blueprint(carriers_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(schedules_bp)
app.register_blueprint(tariffs_bp)
app.register_blueprint(plan_bp)
app.register_blueprint(api_bp)
app.register_blueprint(policies_bp)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
