from app.models.custom import CustomTrip
from app.models.enums import CustomTripType


class TourTrip(CustomTrip):
    """
    Viaje tipo tour: múltiples puntos de destino.
    Puede incluir viáticos del conductor y alquilarse por múltiples días.
    """
    
    __mapper_args__ = {
        "polymorphic_identity": CustomTripType.TOUR
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.custom_trip_type = CustomTripType.TOUR
        if 'rental_days' not in kwargs:
            self.rental_days = 1

    def to_dict(self, include_addresses: bool = True):
        """Serialización para TourTrip."""
        base = super().to_dict(include_addresses=include_addresses)
        base.update({
            "includes_driver_expenses": self.includes_driver_expenses,
            "rental_days": self.rental_days,
            "daily_rate": float(self.daily_rate) if self.daily_rate else None,
        })
        return base

    def validate(self):
        """Validación específica para TourTrip."""
        if len(self.addresses) < 2:
            raise ValueError("TourTrip debe tener al menos 2 direcciones")
        if self.passenger_count < 1:
            raise ValueError("Debe haber al menos 1 pasajero")
        if self.rental_days < 1:
            raise ValueError("El tour debe ser de al menos 1 día")
        if self.daily_rate and self.daily_rate <= 0:
            raise ValueError("La tarifa diaria debe ser mayor a 0")

    def calculate_total_price(self):
        """Calcula el precio total del tour basado en días y tarifa diaria."""
        if self.daily_rate and self.rental_days:
            return float(self.daily_rate) * self.rental_days
        return None