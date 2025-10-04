from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity
from app.controllers.auth_controller import AuthController
from app.middleware import token_required
from app.models.user import User
from app import limiter

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    response, status = AuthController.login(data)
    return jsonify(response), status

@auth_bp.route('/register/traveler', methods=['POST'])
@limiter.limit("3 per hour")
def register_traveler():
    data = request.get_json()
    response, status = AuthController.register_traveler(data)
    return jsonify(response), status

@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh():
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        new_access_token = create_access_token(
            identity=user_id,
            additional_claims={'role': claims.get('role'), 'email': claims.get('email')}
        )
        
        return jsonify({
            'success': True,
            'data': {'access_token': new_access_token}
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error al refrescar token'}), 500

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
