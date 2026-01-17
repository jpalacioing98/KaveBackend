from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity
from app.controllers.auth_controller import AuthController
from app.middleware import token_required
from app.models.user import User
from app import limiter
from datetime import datetime, timezone

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    response, status = AuthController.login(data)
    print(jsonify(response))
    return jsonify(response), status


@auth_bp.route('/register/traveler', methods=['POST'])
@limiter.limit("3 per hour")
def register_traveler():
    data = request.get_json()
    response, status = AuthController.register_traveler(data)
    return jsonify(response), status


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    response, status = AuthController.refresh_token(data)
    return jsonify(response), status


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

        return jsonify({'success': True, 'data': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error del servidor'}), 500


@auth_bp.route('/validate', methods=['GET'])
@token_required
def validate_token():
    data = request.get_json()
    is_expire = AuthController.is_token_expired(data.get('access_token', ''))
    return jsonify({'success': True, 'is_expire': is_expire}), 200
