


from app.models.custom import CustomTrip
from app.models.enums import CustomTripType


class RoundTrip(CustomTrip):
    """
    Viaje de ida y vuelta: de punto A a punto B y regreso a A.
    Permite solicitar tiempo de espera en el destino.
    """
    
    __mapper_args__ = {
        "polymorphic_identity": CustomTripType.ROUND
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.custom_trip_type = CustomTripType.ROUND

    def to_dict(self, include_addresses: bool = True):
        """Serialización para RoundTrip."""
        base = super().to_dict(include_addresses=include_addresses)
        base.update({
            "requires_wait": self.requires_wait,
            "wait_time_minutes": self.wait_time_minutes,
        })
        return base

    def validate(self):
        """Validación específica para RoundTrip."""
        if len(self.addresses) != 2:
            raise ValueError("RoundTrip debe tener exactamente 2 direcciones (origen y destino)")
        if self.passenger_count < 1:
            raise ValueError("Debe haber al menos 1 pasajero")
        if self.requires_wait and (self.wait_time_minutes is None or self.wait_time_minutes <= 0):
            raise ValueError("Si requiere espera, debe especificar un tiempo de espera válido")




