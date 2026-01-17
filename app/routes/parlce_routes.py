from flask import Blueprint
from app.controllers.parcel_controller import create_package_trip,get_package_status,get_driver_packages,get_available_packages,handle_package_request,cancel_package
from app.middleware.auth_middleware import token_required

parcel_bp = Blueprint("parcel_bp", __name__, url_prefix="/api/parcels")

# Create a new parcel
@token_required
@parcel_bp.route("/", methods=["POST"])
def add_parcel():
    return create_package_trip()

# Get parcel status by ID
@token_required
@parcel_bp.route("/<int:parcel_id>/status", methods=["GET"])
def parcel_status(parcel_id):
    return get_package_status(parcel_id)

# List all open parcels
@token_required
@parcel_bp.route("/available", methods=["GET"])
def available_parcels():
    return get_available_packages()

# List parcels for a driver
@token_required
@parcel_bp.route("/driver/<int:driver_id>", methods=["GET"])
def driver_parcels(driver_id):
    return get_driver_packages(driver_id)

# Accept or reject a parcel
@token_required
@parcel_bp.route("/driver/<int:parcel_id>/request", methods=["POST"])
def parcel_request(parcel_id):
    return handle_package_request(parcel_id)

@token_required
@parcel_bp.route('/<int:package_id>/cancel', methods=['PUT'])
def cancel_package_route(package_id):
    return cancel_package(package_id)