from flask import request, jsonify
from app import db
from app.models.custom import CustomTrip
from app.models.enums import CustomTripType, TripStatus, AddressType, TripType
from app.models.one_way import OneWayTrip
from app.models.round import RoundTrip
from app.models.tour import TourTrip

from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from app.models.trip_addresses import Address, TripAddress


class CustomTripController:
    """Controlador para gestionar viajes personalizados."""

    @staticmethod
    def create_custom_trip():
        """
        Crear un nuevo viaje personalizado.
        Espera JSON con:
        {
            "custom_trip_type": "one_way" | "round" | "tour",
            "passenger_count": int,
            "driver_id": int (opcional),
            "vehicle_id": int (opcional),
            "price": float (opcional),
            "notes": str (opcional),
            "departure_time": ISO datetime (opcional),
            "addresses": [
                {
                    "address_text": str,
                    "latitude": float (opcional),
                    "longitude": float (opcional),
                    "type": "pickup" | "delivery" | "waypoint",
                    "order": int
                }
            ],
            // Campos específicos según el tipo:
            // OneWay:
            "allow_shared_ride": bool,
            "is_reserved": bool,
            // Round:
            "requires_wait": bool,
            "wait_time_minutes": int,
            // Tour:
            "includes_driver_expenses": bool,
            "rental_days": int,
            "daily_rate": float
        }
        """
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "No se proporcionaron datos"}), 400

            # Validar tipo de viaje
            custom_trip_type = data.get("custom_trip_type")
            if not custom_trip_type:
                return jsonify({"error": "custom_trip_type es requerido"}), 400

            try:
                trip_type_enum = CustomTripType(custom_trip_type)
            except ValueError:
                return jsonify({
                    "error": f"Tipo de viaje inválido. Debe ser: one_way, round, o tour"
                }), 400

            # Validar direcciones
            addresses_data = data.get("addresses", [])
            if not addresses_data or len(addresses_data) < 2:
                return jsonify({"error": "Se requieren al menos 2 direcciones"}), 400

            # Crear el viaje según el tipo
            trip = None
            if trip_type_enum == CustomTripType.ONE_WAY:
                trip = CustomTripController._create_one_way(data)
            elif trip_type_enum == CustomTripType.ROUND:
                trip = CustomTripController._create_round(data)
            elif trip_type_enum == CustomTripType.TOUR:
                trip = CustomTripController._create_tour(data)

            if not trip:
                return jsonify({"error": "Error al crear el viaje"}), 500

            # Agregar direcciones
            for addr_data in addresses_data:
                address = Address(
                    address_text=addr_data.get("address_text"),
                    latitude=addr_data.get("latitude"),
                    longitude=addr_data.get("longitude"),
                    type=AddressType(addr_data.get("type", "waypoint")),
                    order=addr_data.get("order", 1)
                )
                db.session.add(address)
                db.session.flush()

                trip_address = TripAddress(
                    trip_id=trip.id,
                    address_id=address.id
                )
                db.session.add(trip_address)

            # Validar el viaje
            trip.validate()

            db.session.commit()

            return jsonify({
                "message": "Viaje personalizado creado exitosamente",
                "trip": trip.to_dict()
            }), 201

        except ValueError as ve:
            db.session.rollback()
            return jsonify({"error": str(ve)}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

    @staticmethod
    def _create_one_way(data):
        """Crear viaje OneWay."""
        trip = OneWayTrip(
            trip_type=TripType.CUSTOM,
            passenger_count=data.get("passenger_count", 1),
            driver_id=data.get("driver_id"),
            vehicle_id=data.get("vehicle_id"),
            price=data.get("price"),
            notes=data.get("notes"),
            departure_time=datetime.fromisoformat(
                data["departure_time"]) if data.get("departure_time") else None,
            allow_shared_ride=data.get("allow_shared_ride", False),
            is_reserved=data.get("is_reserved", False),
            status=TripStatus.PENDING
        )
        db.session.add(trip)
        db.session.flush()
        return trip

    @staticmethod
    def _create_round(data):
        """Crear viaje Round."""
        trip = RoundTrip(
            trip_type=TripType.CUSTOM,
            passenger_count=data.get("passenger_count", 1),
            driver_id=data.get("driver_id"),
            vehicle_id=data.get("vehicle_id"),
            price=data.get("price"),
            notes=data.get("notes"),
            departure_time=datetime.fromisoformat(
                data["departure_time"]) if data.get("departure_time") else None,
            requires_wait=data.get("requires_wait", False),
            wait_time_minutes=data.get("wait_time_minutes"),
            status=TripStatus.PENDING
        )
        db.session.add(trip)
        db.session.flush()
        return trip

    @staticmethod
    def _create_tour(data):
        """Crear viaje Tour."""
        trip = TourTrip(
            trip_type=TripType.CUSTOM,
            passenger_count=data.get("passenger_count", 1),
            driver_id=data.get("driver_id"),
            vehicle_id=data.get("vehicle_id"),
            price=data.get("price"),
            notes=data.get("notes"),
            departure_time=datetime.fromisoformat(
                data["departure_time"]) if data.get("departure_time") else None,
            includes_driver_expenses=data.get(
                "includes_driver_expenses", False),
            rental_days=data.get("rental_days", 1),
            daily_rate=data.get("daily_rate"),
            status=TripStatus.PENDING
        )
        db.session.add(trip)
        db.session.flush()
        return trip

    @staticmethod
    def get_custom_trip(trip_id):
        """Obtener un viaje personalizado por ID."""
        try:
            trip = db.session.query(CustomTrip).filter_by(id=trip_id).first()

            if not trip:
                return jsonify({"error": "Viaje no encontrado"}), 404

            return jsonify(trip.to_dict()), 200

        except Exception as e:
            return jsonify({"error": f"Error al obtener el viaje: {str(e)}"}), 500

    @staticmethod
    def get_all_custom_trips():
        """Obtener todos los viajes personalizados con filtros opcionales."""
        try:
            # Parámetros de consulta
            custom_trip_type = request.args.get("custom_trip_type")
            status = request.args.get("status")
            driver_id = request.args.get("driver_id")

            query = db.session.query(CustomTrip)

            # Aplicar filtros
            if custom_trip_type:
                try:
                    query = query.filter_by(
                        custom_trip_type=CustomTripType(custom_trip_type))
                except ValueError:
                    return jsonify({"error": "Tipo de viaje inválido"}), 400

            if status:
                try:
                    query = query.filter_by(status=TripStatus(status))
                except ValueError:
                    return jsonify({"error": "Estado inválido"}), 400

            if driver_id:
                query = query.filter_by(driver_id=int(driver_id))

            trips = query.all()

            return jsonify({
                "count": len(trips),
                "trips": [trip.to_dict() for trip in trips]
            }), 200

        except Exception as e:
            return jsonify({"error": f"Error al obtener viajes: {str(e)}"}), 500

    @staticmethod
    def update_custom_trip(trip_id):
        """
        Actualizar un viaje personalizado.
        Solo permite actualizar campos comunes y específicos del tipo.
        """
        try:
            trip = db.session.query(CustomTrip).filter_by(id=trip_id).first()

            if not trip:
                return jsonify({"error": "Viaje no encontrado"}), 404

            data = request.get_json()
            if not data:
                return jsonify({"error": "No se proporcionaron datos"}), 400

            # Actualizar campos comunes
            if "passenger_count" in data:
                trip.passenger_count = data["passenger_count"]
            if "driver_id" in data:
                trip.driver_id = data["driver_id"]
            if "vehicle_id" in data:
                trip.vehicle_id = data["vehicle_id"]
            if "price" in data:
                trip.price = data["price"]
            if "notes" in data:
                trip.notes = data["notes"]
            if "status" in data:
                trip.status = TripStatus(data["status"])
            if "departure_time" in data:
                trip.departure_time = datetime.fromisoformat(
                    data["departure_time"])
            if "arrival_time" in data:
                trip.arrival_time = datetime.fromisoformat(
                    data["arrival_time"])

            # Actualizar campos específicos según el tipo
            if isinstance(trip, OneWayTrip):
                if "allow_shared_ride" in data:
                    trip.allow_shared_ride = data["allow_shared_ride"]
                if "is_reserved" in data:
                    trip.is_reserved = data["is_reserved"]

            elif isinstance(trip, RoundTrip):
                if "requires_wait" in data:
                    trip.requires_wait = data["requires_wait"]
                if "wait_time_minutes" in data:
                    trip.wait_time_minutes = data["wait_time_minutes"]

            elif isinstance(trip, TourTrip):
                if "includes_driver_expenses" in data:
                    trip.includes_driver_expenses = data["includes_driver_expenses"]
                if "rental_days" in data:
                    trip.rental_days = data["rental_days"]
                if "daily_rate" in data:
                    trip.daily_rate = data["daily_rate"]

            # Validar cambios
            trip.validate()

            db.session.commit()

            return jsonify({
                "message": "Viaje actualizado exitosamente",
                "trip": trip.to_dict()
            }), 200

        except ValueError as ve:
            db.session.rollback()
            return jsonify({"error": str(ve)}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

    @staticmethod
    def delete_custom_trip(trip_id):
        """Eliminar (cancelar) un viaje personalizado."""
        try:
            trip = db.session.query(CustomTrip).filter_by(id=trip_id).first()

            if not trip:
                return jsonify({"error": "Viaje no encontrado"}), 404

            # En lugar de eliminar, marcar como cancelado
            trip.status = TripStatus.CANCELLED
            db.session.commit()

            return jsonify({
                "message": "Viaje cancelado exitosamente",
                "trip": trip.to_dict()
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error al cancelar el viaje: {str(e)}"}), 500

    @staticmethod
    def calculate_tour_price(trip_id):
        """Calcular el precio total de un tour."""
        try:
            trip = db.session.query(TourTrip).filter_by(id=trip_id).first()

            if not trip:
                return jsonify({"error": "Tour no encontrado"}), 404

            total_price = trip.calculate_total_price()

            if total_price is None:
                return jsonify({
                    "error": "No se puede calcular el precio. Falta daily_rate o rental_days"
                }), 400

            return jsonify({
                "trip_id": trip_id,
                "daily_rate": float(trip.daily_rate),
                "rental_days": trip.rental_days,
                "total_price": total_price
            }), 200

        except Exception as e:
            return jsonify({"error": f"Error al calcular precio: {str(e)}"}), 500

    @staticmethod
    def get_driver_trips(driver_id):
        """
        Obtener todos los viajes asignados a un conductor específico.
        Permite filtrar por estado y tipo de viaje.
        """
        try:
            # Parámetros de consulta opcionales
            custom_trip_type = request.args.get("custom_trip_type")
            status = request.args.get("status")

            query = db.session.query(CustomTrip).filter_by(driver_id=driver_id)

            # Aplicar filtros adicionales
            if custom_trip_type:
                try:
                    query = query.filter_by(
                        custom_trip_type=CustomTripType(custom_trip_type))
                except ValueError:
                    return jsonify({"error": "Tipo de viaje inválido"}), 400

            if status:
                try:
                    query = query.filter_by(status=TripStatus(status))
                except ValueError:
                    return jsonify({"error": "Estado inválido"}), 400

            trips = query.order_by(CustomTrip.departure_time.desc()).all()
            pending = []
            history = []

            for p in trips:
                data = p.to_dict()
                print(data.get('status'))
                if data.get('status') == 'Pendiente':
                    pending.append(data)
                elif data.get('status') == 'Finalizado':
                    history.append(data)

            return jsonify({
                "driver_id": driver_id,
                "count": len(trips),
                "pending": pending,
                "history": history
            }), 200

        except Exception as e:
            return jsonify({"error": f"Error al obtener viajes del conductor: {str(e)}"}), 500

    @staticmethod
    def driver_cancel_trip(trip_id):
        """
        Cancelar un viaje por parte del conductor.
        Esto cambia el estado de PENDING a PENDING (disponible),
        elimina el driver_id y vehicle_id, dejando el viaje disponible para otro conductor.
        """
        try:
            trip = db.session.query(CustomTrip).filter_by(id=trip_id).first()

            if not trip:
                return jsonify({"error": "Viaje no encontrado"}), 404

            # Validar que el viaje tenga un conductor asignado
            if not trip.driver_id:
                return jsonify({"error": "Este viaje no tiene conductor asignado"}), 400

            # Obtener el driver_id antes de eliminarlo para el mensaje
            driver_id = trip.driver_id

            # Validar estados permitidos para cancelación por conductor
            allowed_statuses = [TripStatus.PENDING]
            if trip.status not in allowed_statuses:
                return jsonify({
                    "error": f"No se puede cancelar un viaje en estado {trip.status.value}"
                }), 400

            # Liberar el viaje
            trip.driver_id = None
            trip.vehicle_id = None
            trip.status = TripStatus.AVAILABLE

            db.session.commit()

            return jsonify({
                "message": "Viaje liberado exitosamente. Ahora está disponible para otros conductores",
                "trip_id": trip_id,
                "previous_driver_id": driver_id,
                "trip": trip.to_dict()
            }), 200

        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

    # 5️⃣ Aceptar o rechazar un paquete
    @staticmethod
    def handle_trip_request(trip_id):
        """
        Permite que un conductor acepte o rechace un paquete.
        Espera un JSON con:
        - action: "accept" 
        - driver_id (requerido si acepta)
        - vehicle_id (requerido si acepta)
        """
        data = request.get_json()
        action = data.get("action")

        customTrip = CustomTrip.query.get(trip_id)
        if not customTrip:
            return jsonify({"error": "Paquete no encontrado"}), 404

        if customTrip.status not in [ TripStatus.AVAILABLE]:
            print("Este paquete ya fue gestionado")
            return jsonify({"error": "Este paquete ya fue gestionado"}), 400

        if action == "accept":
            driver_id = data.get("driver_id")
            vehicle_id = data.get("vehicle_id")
            if not driver_id:
                print("driver_id requerido para aceptar")
                return jsonify({"error": "driver_id requerido para aceptar"}), 400

            customTrip.driver_id = driver_id
            customTrip.vehicle_id= vehicle_id
            customTrip.status = TripStatus.PENDING
            db.session.commit()
            return jsonify({"message": "Paquete aceptado", "trips": customTrip.to_dict()})

        else:
            print("Acción inválida. Usa 'accept'")
            return jsonify({"error": "Acción inválida. Usa 'accept'."}), 400


