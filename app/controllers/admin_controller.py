

from app.models.user import User
from app.models.admin import Admin
from app.models.driver import Driver
from app.models.superAdmin import SuperUser
from app import db

from app.models.vehicle import Vehicle
from app.utils import Validators

class AdminController:
    
    @staticmethod
    def create_superuser(data):
        try:
            if SuperUser.query.first():
                return {
                    'success': False,
                    'message': 'Ya existe un superusuario en el sistema'
                }, 403
            
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            full_name = data.get('full_name', '').strip()
            phone = data.get('phone', '').strip()
            
            if not email or not password or not full_name:
                return {
                    'success': False,
                    'message': 'Email, contraseña y nombre completo son requeridos'
                }, 400
            
            if not Validators.validate_email(email):
                return {'success': False, 'message': 'Formato de email inválido'}, 400
            
            is_valid, msg = Validators.validate_password(password)
            if not is_valid:
                return {'success': False, 'message': msg}, 400
            
            superuser = SuperUser(email=email, full_name=full_name, phone=phone)
            superuser.set_password(password)
            
            db.session.add(superuser)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Superusuario creado exitosamente',
                'data': superuser.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error: {str(e)}'}, 500
    
    @staticmethod
    def create_admin(data, current_user_id):
        try:
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            full_name = data.get('full_name', '').strip()
            phone = data.get('phone', '').strip()
            permissions = data.get('permissions', ['read', 'write'])
            
            if not email or not password or not full_name:
                return {
                    'success': False,
                    'message': 'Email, contraseña y nombre completo son requeridos'
                }, 400
            
            if not Validators.validate_email(email):
                return {'success': False, 'message': 'Formato de email inválido'}, 400
            
            is_valid, msg = Validators.validate_password(password)
            if not is_valid:
                return {'success': False, 'message': msg}, 400
            
            if User.query.filter_by(email=email).first():
                return {'success': False, 'message': 'El email ya está registrado'}, 409
            
            admin = Admin(
                email=email,
                full_name=full_name,
                phone=phone,
                permissions=permissions,
                created_by=current_user_id
            )
            admin.set_password(password)
            
            db.session.add(admin)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Admin creado exitosamente',
                'data': admin.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error: {str(e)}'}, 500
    
    @staticmethod
    def create_driver(data, current_user_id, current_user_role):
        try:
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            full_name = data.get('full_name', '').strip()
            license_number = data.get('license_number', '').strip()
            phone = data.get('phone', '').strip()
            vehicle_info = data.get('vehicle_info', {})
            
            admin_id = data.get('admin_id')
            
            
            
            if not email or not password or not full_name or not license_number:
                return {
                    'success': False,
                    'message': 'Todos los campos son requeridos'
                }, 400
            
            if not Validators.validate_email(email):
                return {'success': False, 'message': 'Formato de email inválido'}, 400
            
            is_valid, msg = Validators.validate_password(password)
            if not is_valid:
                return {'success': False, 'message': msg}, 400
            
            if User.query.filter_by(email=email).first():
                return {'success': False, 'message': 'El email ya está registrado'}, 409
            
            if Driver.query.filter_by(license_number=license_number).first():
                return {'success': False, 'message': 'Licencia ya registrada'}, 409
            
            if current_user_role == 'admin':
                admin_id = current_user_id
            elif current_user_role == 'superuser' and admin_id:
                pass
            else:
                return {'success': False, 'message': 'Admin ID requerido'}, 400
            
            admin = Admin.query.get(admin_id)
            if not admin:
                return {'success': False, 'message': 'Admin no encontrado'}, 404
            
            driver = Driver(
                email=email,
                full_name=full_name,
                license_number=license_number,
                phone=phone,
                
            )
            driver.set_password(password)
            
            db.session.add(driver)
            db.session.flush()
            
            vehicle = Vehicle(
                make=vehicle_info['make'],
                model=vehicle_info['model'],
                year=vehicle_info['year'],
                color=vehicle_info['color'],
                plate=vehicle_info['plate'],
                seats=vehicle_info['seats'],
                driver_id=driver.id
            )
            db.session.add(vehicle)
            admin.assigned_drivers.append(driver)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Driver creado exitosamente',
                'data': driver.to_dict(include_admins=True)
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error: {str(e)}'}, 500
    
    @staticmethod
    def get_admin_drivers(admin_id, current_user_id, current_user_role):
        try:
            if current_user_role == 'admin' and admin_id != current_user_id:
                return {
                    'success': False,
                    'message': 'No tienes permisos'
                }, 403
            
            admin = Admin.query.get(admin_id)
            if not admin:
                return {'success': False, 'message': 'Admin no encontrado'}, 404
            
            drivers = [driver.to_dict() for driver in admin.assigned_drivers.all()]
            
            return {
                'success': True,
                'data': {
                    'admin': admin.to_dict(),
                    'drivers': drivers,
                    'total_drivers': len(drivers)
                }
            }, 200
            
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500
    
    @staticmethod
    def get_all_admins():
        try:
            admins = Admin.query.all()
            admins_data = [admin.to_dict(include_drivers=True) for admin in admins]
            
            return {
                'success': True,
                'data': {'admins': admins_data, 'total': len(admins_data)}
            }, 200
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500
    
    @staticmethod
    def verify_driver(driver_id, current_user_id, current_user_role, is_verified):
        try:
            driver = Driver.query.get(driver_id)
            if not driver:
                return {'success': False, 'message': 'Driver no encontrado'}, 404
            
            if current_user_role == 'admin':
                admin = Admin.query.get(current_user_id)
                if driver not in admin.assigned_drivers.all():
                    return {'success': False, 'message': 'No tienes permisos'}, 403
            
            driver.is_verified = is_verified
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Driver {"verificado" if is_verified else "desverificado"}',
                'data': driver.to_dict()
            }, 200
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Error: {str(e)}'}, 500
          
            