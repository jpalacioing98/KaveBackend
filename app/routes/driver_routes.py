from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.controllers.driver_controller import DriverController

driver_bp = Blueprint('driver_bp', __name__, url_prefix='/api/driver')


# -------------------------------
#  STATUS
# -------------------------------
@driver_bp.route('/status', methods=['PATCH'])
@jwt_required()
def update_status():
    driver_id = get_jwt_identity()
    data = request.get_json()
    return DriverController.update_status(driver_id, data)


# -------------------------------
#  VIAJES
# -------------------------------
@driver_bp.route('/trips', methods=['GET'])
@jwt_required()
def list_trips():
    driver_id = get_jwt_identity()
    return DriverController.list_trips(driver_id)

@driver_bp.route('/trips/<int:trip_id>/start', methods=['POST'])
@jwt_required()
def start_trip(trip_id):
    driver_id = get_jwt_identity()
    return DriverController.start_trip(trip_id, driver_id)

@driver_bp.route('/trips/<int:trip_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_trip(trip_id):
    driver_id = get_jwt_identity()
    data = request.get_json()
    return DriverController.cancel_trip(trip_id, driver_id, data)

@driver_bp.route('/trips/<int:trip_id>/replacement', methods=['POST'])
@jwt_required()
def request_replacement(trip_id):
    driver_id = get_jwt_identity()
    return DriverController.request_replacement(trip_id, driver_id)


# -------------------------------
#  PASAJEROS
# -------------------------------
@driver_bp.route('/trips/<int:trip_id>/passengers', methods=['GET'])
@jwt_required()
def get_passengers(trip_id):
    driver_id = get_jwt_identity()
    return DriverController.get_passengers(trip_id, driver_id)


# -------------------------------
#  ENCOMIENDAS
# -------------------------------
@driver_bp.route('/packages', methods=['GET'])
@jwt_required()
def list_packages():
    driver_id = get_jwt_identity()
    return DriverController.list_packages(driver_id)

@driver_bp.route('/packages/<int:package_id>/accept', methods=['POST'])
@jwt_required()
def accept_package(package_id):
    driver_id = get_jwt_identity()
    return DriverController.accept_package(package_id, driver_id)


# -------------------------------
#  FLETES
# -------------------------------
@driver_bp.route('/freights', methods=['GET'])
@jwt_required()
def list_freights():
    driver_id = get_jwt_identity()
    return DriverController.list_freights(driver_id)

@driver_bp.route('/freights/<int:freight_id>/accept', methods=['POST'])
@jwt_required()
def accept_freight(freight_id):
    driver_id = get_jwt_identity()
    return DriverController.accept_freight(freight_id, driver_id)
