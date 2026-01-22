from flask import Blueprint
from app.controllers.driver_controller import get_all_drivers, get_drivers_by_status, get_driver_by_id_or_name

driver_bp = Blueprint('drivers', __name__, url_prefix='/api/drivers')

@driver_bp.route('', methods=['GET'])
def fetch_all_drivers():
    return get_all_drivers()

@driver_bp.route('/status/<status>', methods=['GET'])
def fetch_drivers_by_status(status):
    return get_drivers_by_status(status)

@driver_bp.route('/<identifier>', methods=['GET'])
def fetch_driver_by_id_or_name(identifier):
    return get_driver_by_id_or_name(identifier)
