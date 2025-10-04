from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            print("🔑 Token detectado:", claims)
            return fn(*args, **kwargs)
        except Exception as e:
            print("❌ Error en token_required:", e)
            return jsonify({
                'success': False,
                'message': 'Token inválido o expirado'
            }), 401
    return wrapper

def role_required(allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                user_role = claims.get('role')
                
                if user_role not in allowed_roles:
                    return jsonify({
                        'success': False,
                        'message': 'No tienes permisos para acceder a este recurso'
                    }), 403
                
                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': 'Error de autenticación'
                }), 401
        return wrapper
    return decorator

def superuser_required(fn):
    return role_required(['superuser'])(fn)

def admin_required(fn):
    return role_required(['admin'])(fn)

def driver_required(fn):
    return role_required(['driver'])(fn)

def admin_or_superuser_required(fn):
    return role_required(['admin', 'superuser'])(fn)

def staff_required(fn):
    return role_required(['superuser', 'admin', 'driver'])(fn)