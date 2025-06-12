from .locations import bp as locations_bp
from .carriers import bp as carriers_bp
from .routes_view import bp as routes_bp
from .schedules import bp as schedules_bp
from .tariffs import bp as tariffs_bp
from .plan_view import bp as plan_bp
from .api import bp as api_bp
from .policies import bp as policies_bp

__all__ = [
    'locations_bp',
    'carriers_bp',
    'routes_bp',
    'schedules_bp',
    'tariffs_bp',
    'plan_bp',
    'api_bp',
    'policies_bp',
]
