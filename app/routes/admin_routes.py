from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity

from app import limiter
from app.middleware import (
    token_required,
    superuser_required,
    admin_or_superuser_required
)
from app.controllers import AdminController

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/superuser/setup', methods=['POST'])
def setup_superuser():
    data = request.get_json()
    response, status = AdminController.create_superuser(data)
    return jsonify(response), status


@admin_bp.route('/admins', methods=['POST'])
@superuser_required
def create_admin():
    user_id = get_jwt_identity()
    data = request.get_json()
    response, status = AdminController.create_admin(data, user_id)
    return jsonify(response), status

@admin_bp.route('/admins', methods=['GET'])

@superuser_required
def get_all_admins():
    response, status = AdminController.get_all_admins()
    return jsonify(response), status

@admin_bp.route('/drivers', methods=['POST'])
@token_required
@admin_or_superuser_required
def create_driver():
    user_id = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get('role')
    data = request.get_json()
    response, status = AdminController.create_driver(data, user_id, user_role)
    return jsonify(response), status

@admin_bp.route('/admins/<int:admin_id>/drivers', methods=['GET'])
@token_required
@admin_or_superuser_required
def get_admin_drivers(admin_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get('role')
    response, status = AdminController.get_admin_drivers(admin_id, user_id, user_role)
    return jsonify(response), status

@admin_bp.route('/drivers/<int:driver_id>/verify', methods=['PATCH'])
@token_required
@admin_or_superuser_required
def verify_driver(driver_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    user_role = claims.get('role')
    data = request.get_json()
    is_verified = data.get('is_verified', True)
    response, status = AdminController.verify_driver(driver_id, user_id, user_role, is_verified)
    return jsonify(response), status