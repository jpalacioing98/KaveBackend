

from datetime import datetime
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models.driver import Driver
from app.models.enums import AddressType, DriverStatus, TripStatus, TripType
from app.models.package import PackageTrip
from app.models.trip_addresses import Address


def create_package_trip_service(data: dict) -> dict:
    """
    Servicio para crear un viaje de paquete.
    
    Args:
        data: Diccionario con los datos del paquete
        
    Returns:
        dict: Resultado de la operación con 'success', 'data' o 'error'
        
    Raises:
        ValueError: Si faltan campos obligatorios o datos inválidos
        Exception: Otros errores durante la creación
    """
    try:
        # === Validaciones básicas ===
        if not data.get("package_description"):
            raise ValueError("El campo 'package_description' es obligatorio")

        pickup_data = data.get("pickup_address")
        delivery_data = data.get("delivery_address")

        if not pickup_data or not delivery_data:
            raise ValueError("pickup_address y delivery_address son obligatorios")

        # === Crear direcciones ===
        pickup_address = Address(
            address_text=pickup_data["address_text"],
            latitude=pickup_data.get("latitude"),
            longitude=pickup_data.get("longitude"),
            type=AddressType.PICKUP,
            order=1
        )
        delivery_address = Address(
            address_text=delivery_data["address_text"],
            latitude=delivery_data.get("latitude"),
            longitude=delivery_data.get("longitude"),
            type=AddressType.DELIVERY,
            order=2
        )

        db.session.add(pickup_address)
        db.session.add(delivery_address)
        db.session.flush()

        # === Determinar estado inicial según driver_id ===
        driver_id = data.get("selected_driver_id")
        
        # Convertir string "Null" a None
        if driver_id == "Null" or driver_id == "null" or driver_id == "":
            driver_id = None
        
        initial_status = TripStatus.PENDING if driver_id is not None else TripStatus.AVAILABLE

        # === Crear paquete ===
        package_trip = PackageTrip(
            trip_type=TripType.PACKAGE,
            status=initial_status,
            driver_id=driver_id,
            vehicle_id=data.get("selected_driver_vehicle_id"),
            price=data.get("price"),
            notes=data.get("notes"),
            departure_time=datetime.fromisoformat(data["departure_time"]) if data.get("departure_time") else None,
            arrival_time=datetime.fromisoformat(data["arrival_time"]) if data.get("arrival_time") else None,
            package_description=data["package_description"],
            weight=data.get("weight"),
            dimensions=data.get("dimensions"),
            pickup_address_id=pickup_address.id,
            delivery_address_id=delivery_address.id,
            created_at=datetime.utcnow()
        )

        db.session.add(package_trip)
        db.session.commit()

        return {
            "success": True,
            "message": "Paquete creado exitosamente",
            "data": package_trip.to_dict()
        }

    except ValueError as ve:
        db.session.rollback()
        return {
            "success": False,
            "error": str(ve),
            "error_type": "validation"
        }
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "error": str(e),
            "error_type": "server"
        }

# 1️⃣ Crear un paquete
def create_package_trip():
    try:
        data = request.get_json()

        # === Validaciones básicas ===
        if not data.get("package_description"):
            return jsonify({"error": "El campo 'package_description' es obligatorio"}), 400

        pickup_data = data.get("pickup_address")
        delivery_data = data.get("delivery_address")

        if not pickup_data or not delivery_data:
            return jsonify({"error": "pickup_address y delivery_address son obligatorios"}), 400

        # === Crear direcciones ===
        pickup_address = Address(
            address_text=pickup_data["address_text"],
            latitude=pickup_data.get("latitude"),
            longitude=pickup_data.get("longitude"),
            type=AddressType.PICKUP,
            order=1
        )
        delivery_address = Address(
            address_text=delivery_data["address_text"],
            latitude=delivery_data.get("latitude"),
            longitude=delivery_data.get("longitude"),
            type=AddressType.DELIVERY,
            order=2
        )

        db.session.add(pickup_address)
        db.session.add(delivery_address)
        db.session.flush()

        # === Determinar estado inicial según driver_id ===
        driver_id = data.get("driver_id")
        
        # Convertir string "Null" a None
        if driver_id == "Null" or driver_id == "null" or driver_id == "":
            driver_id = None
        
        initial_status = TripStatus.PENDING if driver_id is not None else TripStatus.AVAILABLE

        # === Crear paquete ===
        package_trip = PackageTrip(
            trip_type=TripType.PACKAGE,
            status=initial_status,
            driver_id=driver_id,  # Ahora será None o un ID válido
            vehicle_id=data.get("vehicle_id"),
            price=data.get("price"),
            notes=data.get("notes"),
            departure_time=datetime.fromisoformat(data["departure_time"]) if data.get("departure_time") else None,
            arrival_time=datetime.fromisoformat(data["arrival_time"]) if data.get("arrival_time") else None,
            package_description=data["package_description"],
            weight=data.get("weight"),
            dimensions=data.get("dimensions"),
            pickup_address_id=pickup_address.id,
            delivery_address_id=delivery_address.id,
            created_at=datetime.utcnow()
        )

        db.session.add(package_trip)
        db.session.commit()

        return jsonify({
            "message": "Paquete creado exitosamente",
            "package_trip": package_trip.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 2️⃣ Consultar el estado de un paquete
def get_package_status(package_id):
    package = PackageTrip.query.get(package_id)
    if not package:
        return jsonify({"error": "Paquete no encontrado"}), 404

    return jsonify({
        "id": package.id,
        "status": package.status.value,
        "description": package.package_description
    })


# 3️⃣ Listar todos los paquetes disponibles
def get_available_packages():
    packages = PackageTrip.query.filter_by(status=TripStatus.AVAILABLE).all()
    return jsonify([p.to_dict() for p in packages])


# 4️⃣ Listar paquetes por conductor
def get_driver_packages(driver_id):
    packages = PackageTrip.query.filter_by(driver_id=driver_id).all()

    pending = []
    history = []

    for p in packages:
        data = p.to_dict()
        print(data.get('status'))
        if data.get('status') == 'Pendiente':
            pending.append(data)
        elif data.get('status') == 'Finalizado':
            history.append(data)

    return jsonify({
        "pending": pending,
        "history": history
    })


# 5️⃣ Aceptar o rechazar un paquete
def handle_package_request(package_id):
    """
    Permite que un conductor acepte o rechace un paquete.
    Espera un JSON con:
      - action: "accept" 
      - driver_id (requerido si acepta)
      - vehicle_id (requerido si acepta)
    """
    data = request.get_json()
    action = data.get("action")

    package = PackageTrip.query.get(package_id)
    if not package:
        return jsonify({"error": "Paquete no encontrado"}), 404

    if package.status not in [ TripStatus.AVAILABLE]:
        print("Este paquete ya fue gestionado")
        return jsonify({"error": "Este paquete ya fue gestionado"}), 400

    if action == "accept":
        driver_id = data.get("driver_id")
        vehicle_id = data.get("vehicle_id")
        if not driver_id:
            print("driver_id requerido para aceptar")
            return jsonify({"error": "driver_id requerido para aceptar"}), 400

        package.driver_id = driver_id
        package.vehicle_id= vehicle_id
        package.status = TripStatus.PENDING
        db.session.commit()
        return jsonify({"message": "Paquete aceptado", "package_trip": package.to_dict()})

    else:
        print("Acción inválida. Usa 'accept'")
        return jsonify({"error": "Acción inválida. Usa 'accept'."}), 400

# 6️⃣ Cancelar un paquete asignado
def cancel_package(package_id):
    """
    Cancela un paquete asignado, cambiando su estado de PENDING a AVAILABLE
    y limpiando los campos driver_id y vehicle_id.
    """
    try:
        package = PackageTrip.query.get(package_id)
        
        if not package:
            return jsonify({"error": "Paquete no encontrado"}), 404

        # Validar que el paquete esté en estado PENDING
        if package.status != TripStatus.PENDING:
            return jsonify({
                "error": f"Solo se pueden cancelar paquetes en estado PENDING. Estado actual: {package.status.value}"
            }), 400

        # Cancelar la asignación
        package.status = TripStatus.AVAILABLE
        package.driver_id = None
        package.vehicle_id = None
        
        db.session.commit()

        return jsonify({
            "message": "Paquete cancelado exitosamente",
            "package_trip": package.to_dict()
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    