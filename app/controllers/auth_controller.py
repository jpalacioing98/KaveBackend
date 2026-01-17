from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from datetime import datetime
import re
from app.models.user import User

from app.models.traveler import Traveler
from app import db
from app.utils import Validators

class AuthController:
    
    @staticmethod
    def login(data):
        """
        🔥 CAMBIO V7: Ya no se requiere el campo 'role' en la petición.
        El rol se detecta automáticamente desde la base de datos.
        """
        try:
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            
            if not email or not password:
                return {
                    'success': False,
                    'message': 'Email y contraseña son requeridos'
                }, 400
            
            if not Validators.validate_email(email):
                return {
                    'success': False,
                    'message': 'Formato de email inválido'
                }, 400
            
            # 🔥 CAMBIO V7: Buscar usuario solo por email (sin filtrar por rol)
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return {
                    'success': False,
                    'message': 'Credenciales inválidas'
                }, 401
            
            if not user.is_active:
                return {
                    'success': False,
                    'message': 'Cuenta desactivada. Contacta al administrador'
                }, 403
            
            if user.is_locked():
                return {
                    'success': False,
                    'message': 'Cuenta bloqueada por múltiples intentos fallidos'
                }, 403
            
            if not user.check_password(password):
                user.increment_failed_login()
                db.session.commit()
                return {
                    'success': False,
                    'message': 'Credenciales inválidas'
                }, 401
            
            user.reset_failed_login()
            user.update_last_login()
            db.session.commit()
            
            # 🔥 CAMBIO V7: El rol se obtiene automáticamente del usuario
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={'role': user.role, 'email': user.email}
            )
            refresh_token = create_refresh_token(
                identity=str(user.id),
                additional_claims={'role': user.role}
            )
            
            
            return {
                'success': True,
                'message': 'Login exitoso',
                'data': {
                    'user': user.to_dict(),
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            }, 200
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error en el servidor: {str(e)}'
            }, 500
    
    @staticmethod
    def register_traveler(data):
        try:
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            full_name = data.get('full_name', '').strip()
            phone = data.get('phone', '').strip()
            date_of_birth = data.get('date_of_birth')
            emergency_contact = data.get('emergency_contact', {})
            
            if not email or not password or not full_name:
                return {
                    'success': False,
                    'message': 'Email, contraseña y nombre completo son requeridos'
                }, 400
            
            if not Validators.validate_email(email):
                return {
                    'success': False,
                    'message': 'Formato de email inválido'
                }, 400
            
            is_valid, msg = Validators.validate_password(password)
            if not is_valid:
                return {'success': False, 'message': msg}, 400
            
            if User.query.filter_by(email=email).first():
                return {
                    'success': False,
                    'message': 'El email ya está registrado'
                }, 409
            
            traveler = Traveler(
                email=email,
                full_name=full_name,
                phone=phone,
                emergency_contact=emergency_contact
            )
            
            if date_of_birth:
                try:
                    traveler.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                except:
                    pass
            
            traveler.set_password(password)
            db.session.add(traveler)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Viajero registrado exitosamente',
                'data': traveler.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Error en el servidor: {str(e)}'
            }, 500            

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Devuelve True si el token está expirado o es inválido.

        Usa `decode_token` con `allow_expired=True` para leer la claim `exp` y compararla
        con el tiempo actual en UTC. Si el token no puede decodificarse se considera inválido
        (y por lo tanto tratado como expirado/rechazado).
        """
        try:
            # Soportar encabezados tipo "Bearer <token>"
            if isinstance(token, str) and token.lower().startswith('bearer '):
                token = token.split(' ', 1)[1].strip()

            decoded = decode_token(token, allow_expired=True)
            exp = decoded.get('exp')
            if exp is None:
                # Si no tiene exp, lo tratamos como inválido/expirado
                return True
            # exp es un timestamp en segundos (UTC)
            now_ts = datetime.utcnow().timestamp()
            return now_ts > exp
        except Exception:
            # Cualquier error al decodificar -> token inválido/expirado
            return True

    @staticmethod
    def refresh_tokens(refresh_token: str):
        """Refresca access y refresh tokens a partir de un refresh token válido.

        Flujo:
        - Decodifica y valida que el token sea de tipo 'refresh'.
        - Obtiene la identidad (sub) y busca el usuario.
        - Comprueba que el usuario exista y esté activo/no bloqueado.
        - Genera y devuelve nuevos access_token y refresh_token.

        Retorna una tupla (payload_dict, status_code) al estilo del resto del controller.
        """
        try:
            # Soportar encabezados "Bearer <token>"
            if isinstance(refresh_token, str) and refresh_token.lower().startswith('bearer '):
                refresh_token = refresh_token.split(' ', 1)[1].strip()

            # Esto valida firma y expiración (allow_expired=False)
            decoded = decode_token(refresh_token, allow_expired=False)
        except Exception as e:
            return {
                'success': False,
                'message': 'Refresh token inválido o expirado'
            }, 401
        # Algunos formatos usan 'type' o 'token_type'
        token_type = decoded.get('type') or decoded.get('token_type')
        if token_type != 'refresh':
            return {
                'success': False,
                'message': 'El token proporcionado no es un refresh token'
            }, 400
        identity = decoded.get('sub') or decoded.get('identity') or decoded.get('user_id')
        if not identity:
            return {
                'success': False,
                'message': 'Identidad no encontrada en el token'
            }, 400

        # Intentar obtener el usuario (identity fue guardado como str(user.id) en login)
        try:
            user_id = int(identity)
        except Exception:
            return {
                'success': False,
                'message': 'Identidad de token inválida'
            }, 400

        user = User.query.get(user_id)
        if not user:
            return {
                'success': False,
                'message': 'Usuario no encontrado'
            }, 404

        if not user.is_active:
            return {
                'success': False,
                'message': 'Cuenta desactivada. Contacta al administrador'
            }, 403

        if user.is_locked():
            return {
                'success': False,
                'message': 'Cuenta bloqueada'
            }, 403

        # Generar nuevos tokens con claims actualizados
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'email': user.email}
        )
        new_refresh = create_refresh_token(
            identity=str(user.id),
            additional_claims={'role': user.role}
        )

        return {
            'success': True,
            'message': 'Tokens refrescados correctamente',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': new_refresh
            }
        }, 200
            
            
            
