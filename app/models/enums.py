from enum import Enum


class TripType(str, Enum):
    """Different types of trips"""
    NORMAL = "normal"        # Passenger transport
    PACKAGE = "package"      # Parcel delivery
    CUSTOM = "Custom"      # Full-load or rapid trip


class CustomTripType(Enum):
    ONE_WAY = "one_way"
    ROUND = "round"
    TOUR = "tour"


class TripStatus(str, Enum):
    """Possible trip statuses"""
    AVAILABLE = "Disponible"
    PENDING = "Pendiente"
    IN_PROGRESS = "En progreso"
    FINISHED = "Finalizado"
    CANCELED = "Cancelado"


class AddressType(str, Enum):
    """Address usage type"""
    PICKUP = "pickup"
    DELIVERY = "delivery"
    WAYPOINT = "waypoint"


class FreightMode(str, Enum):
    """Freight trip mode"""
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


class DriverStatus(Enum):
    AVAILABLE = "disponible"         # El conductor está libre y puede recibir solicitudes
    # Tiene una solicitud o paquete asignado, pero aún no ha iniciado
    ASSIGNED = "asignado"
    ON_TRIP = "en_viaje"             # Está realizando un viaje actualmente
    # No está disponible (fuera de servicio o no conectado)
    OFFLINE = "desconectado"
    BUSY = "ocupado"                 # Ocupado en otra tarea o entrega
    SUSPENDED = "suspendido"         # Temporalmente inactivo por decisión administrativa
