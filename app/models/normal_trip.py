
from app import db
from app.models.enums import  TripType
from app.models.trip import Trip

class NormalTrip(Trip):
    __tablename__ = "normal_trips"

    id = db.Column(db.Integer, db.ForeignKey("trips.id"), primary_key=True)
    available_seats = db.Column(db.Integer, default=0)

    __mapper_args__ = {
        "polymorphic_identity": TripType.NORMAL
    }

    def __repr__(self):
        return f"<NormalTrip(id={self.id}, seats={self.available_seats})>"

    def to_dict(self, include_addresses: bool = True):
        """
        Extend Trip.to_dict() with NormalTrip-specific fields.
        """
        data = super().to_dict(include_addresses=include_addresses)
        data.update({
            "available_seats": self.available_seats,
        })
        return data