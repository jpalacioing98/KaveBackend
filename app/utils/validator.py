import re

class Validators:
    
    @staticmethod
    def validate_email(email):
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Valida fortaleza de contraseña"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe contener al menos una mayúscula"
        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe contener al menos una minúscula"
        if not re.search(r'\d', password):
            return False, "La contraseña debe contener al menos un número"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "La contraseña debe contener al menos un carácter especial"
        return True, "OK"
    
    @staticmethod
    def validate_role(role):
        """Valida que el rol sea válido"""
        valid_roles = ['superuser', 'admin', 'driver', 'traveler']
        return role in valid_roles