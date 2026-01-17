
from app import db
from app.models.enums import  CustomTripType, TripType
from app.models.trip import Trip

class CustomTrip(Trip):
    """
    Modelo base para viajes personalizados.
    Utiliza herencia de tabla única (Single Table Inheritance) con discriminador en custom_trip_type.
    """
    __tablename__ = "custom_trips"
    
    id = db.Column(db.Integer, db.ForeignKey("trips.id"), primary_key=True)
    custom_trip_type = db.Column(db.Enum(CustomTripType), nullable=False)
    passenger_count = db.Column(db.Integer, nullable=False, default=1)
    
    # Campos específicos para OneWay
    allow_shared_ride = db.Column(db.Boolean, default=False, nullable=True)
    is_reserved = db.Column(db.Boolean, default=False, nullable=True)
    
    # Campos específicos para Round
    requires_wait = db.Column(db.Boolean, default=False, nullable=True)
    wait_time_minutes = db.Column(db.Integer, nullable=True)
    
    # Campos específicos para Tour
    includes_driver_expenses = db.Column(db.Boolean, default=False, nullable=True)
    rental_days = db.Column(db.Integer, default=1, nullable=True)
    daily_rate = db.Column(db.Numeric(10, 2), nullable=True)
    
    __mapper_args__ = {
        "polymorphic_identity": TripType.CUSTOM,
        "polymorphic_on": custom_trip_type
    }

    def __repr__(self):
        return f"<CustomTrip(id={self.id}, type={self.custom_trip_type.value if self.custom_trip_type else None}, passengers={self.passenger_count})>"

    def to_dict(self, include_addresses: bool = True):
        """Serialización base de CustomTrip."""
        base = super().to_dict(include_addresses=include_addresses)
        base.update({
            "custom_trip_type": self.custom_trip_type.value if self.custom_trip_type else None,
            "passenger_count": self.passenger_count,
        })
        return base