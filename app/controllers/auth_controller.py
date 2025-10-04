from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime
import re
from app.models.user import User
from app.models.admin import Admin
from app.models.driver import Driver
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
            
            
            
