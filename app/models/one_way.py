
from app.models.custom import CustomTrip
from app.models.enums import CustomTripType


class OneWayTrip(CustomTrip):
    """
    Viaje de ida: de punto A a punto B.
    Permite compartir viaje con otros pasajeros o ser reservado exclusivamente.
    """
    
    __mapper_args__ = {
        "polymorphic_identity": CustomTripType.ONE_WAY
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.custom_trip_type = CustomTripType.ONE_WAY

    def to_dict(self, include_addresses: bool = True):
        """Serialización para OneWayTrip."""
        base = super().to_dict(include_addresses=include_addresses)
        base.update({
            "allow_shared_ride": self.allow_shared_ride,
            "is_reserved": self.is_reserved,
        })
        return base

    def validate(self):
        """Validación específica para OneWayTrip."""
        if len(self.addresses) != 2:
            raise ValueError("OneWayTrip debe tener exactamente 2 direcciones (origen y destino)")
        if self.passenger_count < 1:
            raise ValueError("Debe haber al menos 1 pasajero")
        if self.is_reserved and self.allow_shared_ride:
            raise ValueError("Un viaje reservado no puede permitir pasajeros compartidos")
