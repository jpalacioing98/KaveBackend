from app import db
db.create_all()


# ============================================================================
# EJEMPLOS DE USO - POSTMAN/THUNDER CLIENT
# ============================================================================

"""
═══════════════════════════════════════════════════════════════════════════
1. SETUP INICIAL - CREAR SUPERUSUARIO
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/admin/superuser/setup
Content-Type: application/json

{
    "email": "superadmin@sistema.com",
    "password": "SuperSecure123!",
    "full_name": "Super Administrador",
    "phone": "+57 300 1234567"
}

═══════════════════════════════════════════════════════════════════════════
2. LOGIN SUPERUSUARIO
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
    "email": "superadmin@sistema.com",
    "password": "SuperSecure123!",
    "role": "superuser"
}

RESPUESTA:
{
    "success": true,
    "message": "Login exitoso",
    "data": {
        "user": {...},
        "access_token": "eyJ...",
        "refresh_token": "eyJ..."
    }
}

═══════════════════════════════════════════════════════════════════════════
3. CREAR ADMIN 1 - Carlos Rodríguez
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/admin/admins
Authorization: Bearer {superuser_token}
Content-Type: application/json

{
    "email": "admin1@sistema.com",
    "password": "Admin123Secure!",
    "full_name": "Carlos Rodríguez",
    "phone": "+57 310 1111111",
    "permissions": ["read", "write", "delete"]
}

═══════════════════════════════════════════════════════════════════════════
4. CREAR ADMIN 2 - María González
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/admin/admins
Authorization: Bearer {superuser_token}
Content-Type: application/json

{
    "email": "admin2@sistema.com",
    "password": "Admin456Secure!",
    "full_name": "María González",
    "phone": "+57 310 2222222",
    "permissions": ["read", "write"]
}

═══════════════════════════════════════════════════════════════════════════
5. LOGIN ADMIN 1
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
    "email": "admin1@sistema.com",
    "password": "Admin123Secure!",
    "role": "admin"
}

═══════════════════════════════════════════════════════════════════════════
6. CREAR DRIVER 1 PARA ADMIN 1 - Juan Pérez
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/admin/drivers
Authorization: Bearer {admin1_token}
Content-Type: application/json

{
    "email": "driver1.admin1@sistema.com",
    "password": "Driver123Secure!",
    "full_name": "Juan Pérez",
    "license_number": "LIC-2024-001",
    "phone": "+57 320 3333333",
    "vehicle_info": {
        "brand": "Chevrolet",
        "model": "Spark GT",
        "year": 2023,
        "plate": "ABC123",
        "color": "Blanco"
    }
}

═══════════════════════════════════════════════════════════════════════════
7. CREAR DRIVER 2 PARA ADMIN 1 - Pedro Martínez
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/admin/drivers
Authorization: Bearer {admin1_token}
Content-Type: application/json

{
    "email": "driver2.admin1@sistema.com",
    "password": "Driver456Secure!",
    "full_name": "Pedro Martínez",
    "license_number": "LIC-2024-002",
    "phone": "+57 320 4444444",
    "vehicle_info": {
        "brand": "Renault",
        "model": "Logan",
        "year": 2022,
        "plate": "DEF456",
        "color": "Gris"
    }
}

═══════════════════════════════════════════════════════════════════════════
8. LOGIN ADMIN 2
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
    "email": "admin2@sistema.com",
    "password": "Admin456Secure!",
    "role": "admin"
}

═══════════════════════════════════════════════════════════════════════════
9. CREAR DRIVER 1 PARA ADMIN 2 - Ana López
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/admin/drivers
Authorization: Bearer {admin2_token}
Content-Type: application/json

{
    "email": "driver1.admin2@sistema.com",
    "password": "Driver789Secure!",
    "full_name": "Ana López",
    "license_number": "LIC-2024-003",
    "phone": "+57 320 5555555",
    "vehicle_info": {
        "brand": "Mazda",
        "model": "2",
        "year": 2023,
        "plate": "GHI789",
        "color": "Rojo"
    }
}

═══════════════════════════════════════════════════════════════════════════
10. CREAR DRIVER 2 PARA ADMIN 2 - Luis Ramírez
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/admin/drivers
Authorization: Bearer {admin2_token}
Content-Type: application/json

{
    "email": "driver2.admin2@sistema.com",
    "password": "Driver101Secure!",
    "full_name": "Luis Ramírez",
    "license_number": "LIC-2024-004",
    "phone": "+57 320 6666666",
    "vehicle_info": {
        "brand": "Kia",
        "model": "Picanto",
        "year": 2024,
        "plate": "JKL012",
        "color": "Azul"
    }
}

═══════════════════════════════════════════════════════════════════════════
11. VER DRIVERS DE ADMIN 1
═══════════════════════════════════════════════════════════════════════════
GET http://localhost:5000/api/admin/admins/1/drivers
Authorization: Bearer {admin1_token}

═══════════════════════════════════════════════════════════════════════════
12. VERIFICAR UN DRIVER
═══════════════════════════════════════════════════════════════════════════
PATCH http://localhost:5000/api/admin/drivers/1/verify
Authorization: Bearer {admin1_token}
Content-Type: application/json

{
    "is_verified": true
}

═══════════════════════════════════════════════════════════════════════════
13. VER TODOS LOS ADMINS (SOLO SUPERUSER)
═══════════════════════════════════════════════════════════════════════════
GET http://localhost:5000/api/admin/admins
Authorization: Bearer {superuser_token}

═══════════════════════════════════════════════════════════════════════════
14. REGISTRO PÚBLICO DE VIAJERO
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/auth/register/traveler
Content-Type: application/json

{
    "email": "viajero1@email.com",
    "password": "Traveler123!",
    "full_name": "Sofía Hernández",
    "phone": "+57 315 7777777",
    "date_of_birth": "1995-05-15",
    "emergency_contact": {
        "name": "Roberto Hernández",
        "phone": "+57 315 8888888",
        "relationship": "Padre"
    }
}

═══════════════════════════════════════════════════════════════════════════
15. LOGIN DRIVER
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
    "email": "driver1.admin1@sistema.com",
    "password": "Driver123Secure!",
    "role": "driver"
}

═══════════════════════════════════════════════════════════════════════════
16. LOGIN VIAJERO
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
    "email": "viajero1@email.com",
    "password": "Traveler123!",
    "role": "traveler"
}

═══════════════════════════════════════════════════════════════════════════
17. VER MI INFORMACIÓN (CUALQUIER USUARIO)
═══════════════════════════════════════════════════════════════════════════
GET http://localhost:5000/api/auth/me
Authorization: Bearer {any_user_token}

═══════════════════════════════════════════════════════════════════════════
18. REFRESCAR TOKEN
═══════════════════════════════════════════════════════════════════════════
POST http://localhost:5000/api/auth/refresh
Authorization: Bearer {refresh_token}







[
  {
    "package_description": "Caja con documentos importantes",
    "weight": 2.5,
    "dimensions": "30x20x10 cm",
    "pickup_address": {
      "address_text": "Calle 45 #12-33, Bogotá",
      "latitude": 4.648283,
      "longitude": -74.247894,
      "type": "pickup"
    },
    "delivery_address": {
      "address_text": "Carrera 10 #80-20, Bogotá",
      "latitude": 4.667821,
      "longitude": -74.056937,
      "type": "delivery"
    }
  },
  {
    "package_description": "Paquete de repuestos mecánicos",
    "weight": 8.2,
    "dimensions": "60x40x30 cm",
    "pickup_address": {
      "address_text": "Av. Boyacá #25-12, Bogotá",
      "latitude": 4.620982,
      "longitude": -74.123422,
      "type": "pickup"
    },
    "delivery_address": {
      "address_text": "Cra 70 #100-23, Bogotá",
      "latitude": 4.701112,
      "longitude": -74.097234,
      "type": "delivery"
    }
  },
  {
    "package_description": "Sobre con contrato firmado",
    "weight": 0.3,
    "dimensions": "A4",
    "pickup_address": {
      "address_text": "Calle 72 #15-30, Bogotá",
      "latitude": 4.659891,
      "longitude": -74.059742,
      "type": "pickup"
    },
    "delivery_address": {
      "address_text": "Calle 100 #11B-45, Bogotá",
      "latitude": 4.684221,
      "longitude": -74.043901,
      "type": "delivery"
    },
    "assigned_driver_id": 7
  },
  {
    "package_description": "Caja pequeña con accesorios electrónicos",
    "weight": 1.8,
    "dimensions": "25x25x20 cm",
    "pickup_address": {
      "address_text": "Calle 50 #22-10, Bogotá",
      "latitude": 4.632132,
      "longitude": -74.081234,
      "type": "pickup"
    },
    "delivery_address": {
      "address_text": "Cra 15 #120-22, Bogotá",
      "latitude": 4.699142,
      "longitude": -74.038954,
      "type": "delivery"
    },
    "assigned_driver_id": 7
  },
  {
    "package_description": "Caja mediana con ropa",
    "weight": 4.0,
    "dimensions": "50x35x25 cm",
    "pickup_address": {
      "address_text": "Transversal 27 #45-19, Bogotá",
      "latitude": 4.628882,
      "longitude": -74.094521,
      "type": "pickup"
    },
    "delivery_address": {
      "address_text": "Calle 85 #14-45, Bogotá",
      "latitude": 4.671441,
      "longitude": -74.053871,
      "type": "delivery"
    }
  }
]

"""