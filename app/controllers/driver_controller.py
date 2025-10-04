from datetime import datetime
from app import db
from app.models.driver import Driver
from app.models.trip import Trip
from app.models.passenger_assignment import PassengerAssignment
from app.models.package import Package
from app.models.freight import Freight
from app.models.driver_status import DriverStatus
from app.utils.geo import order_waypoints_by_nearest


class DriverController:
    """Lógica de negocio para conductores."""

    # -------------------------------
    #  STATUS
    # -------------------------------
    @staticmethod
    def update_status(driver_id, data):
        """Actualiza el estado actual del conductor."""
        driver = Driver.query.get(driver_id)
        if not driver:
            return {'success': False, 'message': 'Conductor no encontrado'}, 404

        status = data.get('status')
        location = data.get('location')
        route = data.get('route')

        allowed_status = [
            'disponible', 'en_camino', 'ocupado', 'en_turno', 'fuera_de_servicio'
        ]
        if status not in allowed_status:
            return {'success': False, 'message': 'Estado inválido'}, 400

        current = DriverStatus.query.filter_by(driver_id=driver_id).first()
        if not current:
            current = DriverStatus(driver_id=driver_id)
            db.session.add(current)

        current.status = status
        current.location = location
        current.route = route
        current.updated_at = datetime.utcnow()
        db.session.commit()

        return {
            'success': True,
            'message': 'Estado actualizado',
            'data': current.to_dict()
        }, 200

    # -------------------------------
    #  VIAJES
    # -------------------------------
    @staticmethod
    def list_trips(driver_id):
        """Lista viajes del conductor."""
        trips = Trip.query.filter_by(driver_id=driver_id).order_by(Trip.start_time.desc()).all()
        data = [trip.to_dict() for trip in trips]
        return {'success': True, 'data': data}, 200

    @staticmethod
    def start_trip(trip_id, driver_id):
        """Inicia un viaje y ordena las recogidas."""
        trip = Trip.query.get(trip_id)
        if not trip or trip.driver_id != driver_id:
            return {'success': False, 'message': 'No autorizado o viaje no encontrado'}, 404

        if trip.status not in ['Pendiente', 'En curso']:
            return {'success': False, 'message': 'No se puede iniciar este viaje'}, 400

        # Obtener coordenadas del conductor
        driver_status = DriverStatus.query.filter_by(driver_id=driver_id).first()
        if not driver_status or not driver_status.location:
            return {'success': False, 'message': 'Ubicación del conductor no disponible'}, 400

        # Calcular orden de recogida
        waypoints = []
        for assignment in trip.passengers:
            waypoints.append({
                'assignment_id': assignment.id,
                'lat': assignment.pickup_lat,
                'lng': assignment.pickup_lng
            })

        ordered = order_waypoints_by_nearest(0, 0, waypoints)  # Ajusta si manejas lat/lng real
        for idx, w in enumerate(ordered):
            assignment = PassengerAssignment.query.get(w['assignment_id'])
            assignment.order = idx + 1

        trip.status = 'En curso'
        trip.start_time = datetime.utcnow()
        db.session.commit()

        return {
            'success': True,
            'message': 'Viaje iniciado correctamente',
            'data': trip.to_dict()
        }, 200

    @staticmethod
    def cancel_trip(trip_id, driver_id, data):
        """Cancelar viaje por parte del conductor."""
        trip = Trip.query.get(trip_id)
        if not trip or trip.driver_id != driver_id:
            return {'success': False, 'message': 'No autorizado o viaje no encontrado'}, 404
        reason = data.get('reason')
        trip.status = 'Cancelado'
        trip.end_time = datetime.utcnow()
        db.session.commit()
        return {'success': True, 'message': 'Viaje cancelado'}, 200

    @staticmethod
    def request_replacement(trip_id, driver_id):
        """Solicita reemplazo del conductor."""
        trip = Trip.query.get(trip_id)
        if not trip or trip.driver_id != driver_id:
            return {'success': False, 'message': 'No autorizado o viaje no encontrado'}, 404
        trip.status = 'En reemplazo'
        db.session.commit()
        return {'success': True, 'message': 'Solicitud de reemplazo enviada'}, 200

    # -------------------------------
    #  PASAJEROS
    # -------------------------------
    @staticmethod
    def get_passengers(trip_id, driver_id):
        """Lista pasajeros asignados a un viaje."""
        trip = Trip.query.get(trip_id)
        if not trip or trip.driver_id != driver_id:
            return {'success': False, 'message': 'No autorizado o viaje no encontrado'}, 404
        passengers = [p.to_dict() for p in trip.passengers]
        return {'success': True, 'data': passengers}, 200

    # -------------------------------
    #  ENCOMIENDAS
    # -------------------------------
    @staticmethod
    def list_packages(driver_id):
        """Lista encomiendas asignadas o pendientes."""
        packages = Package.query.filter(
            (Package.driver_id == driver_id) | (Package.status == 'Pendiente')
        ).all()
        return {'success': True, 'data': [p.to_dict() for p in packages]}, 200

    @staticmethod
    def accept_package(package_id, driver_id):
        """Acepta una encomienda."""
        package = Package.query.get(package_id)
        if not package:
            return {'success': False, 'message': 'Encomienda no encontrada'}, 404
        package.driver_id = driver_id
        package.status = 'Aceptada'
        db.session.commit()
        return {'success': True, 'message': 'Encomienda aceptada'}, 200

    # -------------------------------
    #  FLETES
    # -------------------------------
    @staticmethod
    def list_freights(driver_id):
        freights = Freight.query.filter(
            (Freight.driver_id == driver_id) | (Freight.status == 'Pendiente')
        ).all()
        return {'success': True, 'data': [f.to_dict() for f in freights]}, 200

    @staticmethod
    def accept_freight(freight_id, driver_id):
        freight = Freight.query.get(freight_id)
        if not freight:
            return {'success': False, 'message': 'Flete no encontrado'}, 404
        freight.driver_id = driver_id
        freight.status = 'Aceptado'
        db.session.commit()
        return {'success': True, 'message': 'Flete aceptado'}, 200
