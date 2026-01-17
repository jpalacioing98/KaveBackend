

from datetime import datetime
from app import db
from app.models.enums import TripStatus, TripType


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)
    trip_type = db.Column(db.Enum(TripType), nullable=False)
    status = db.Column(db.Enum(TripStatus), default=TripStatus.PENDING)
    driver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    vehicle_id = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    departure_time = db.Column(db.DateTime, nullable=True)
    arrival_time = db.Column(db.DateTime, nullable=True)

    # Relationships
    addresses = db.relationship("TripAddress", back_populates="trip")

    __mapper_args__ = {
        "polymorphic_identity": "trip",
        "polymorphic_on": trip_type
    }

    def __repr__(self):
        return f"<Trip(id={self.id}, type={self.trip_type.value}, status={self.status.value})>"

    def to_dict(self, include_addresses: bool = True):
        """
        Base serializable representation for Trip.
        include_addresses: if True, include trip_addresses list.
        """
        base = {
            "id": self.id,
            "trip_type": self.trip_type.value if self.trip_type is not None else None,
            "status": self.status.value if self.status is not None else None,
            "driver_id": self.driver_id,
            "vehicle_id": self.vehicle_id,
            "price": float(self.price) if self.price is not None else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "departure_time": self.departure_time.isoformat() if self.departure_time else None,
            "arrival_time": self.arrival_time.isoformat() if self.arrival_time else None,
        }

        if include_addresses:
            # Represent associated TripAddress entries (safe, minimal)
            base["trip_addresses"] = [ta.to_dict() for ta in (self.addresses or [])]

        return base
