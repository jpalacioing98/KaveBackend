
from app import db
from app.models.enums import AddressType



class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    address_text = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    type = db.Column(db.Enum(AddressType), nullable=False)
    order = db.Column(db.Integer, default=1)

    # Relationships
    trips = db.relationship("TripAddress", back_populates="address")

    def __repr__(self):
        return f"<Address(id={self.id}, type={self.type}, text='{self.address_text}')>"

    def to_dict(self):
        """Return a serializable dict for Address."""
        return {
            "id": self.id,
            "address_text": self.address_text,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "type": self.type if isinstance(self.type, str) else self.type.value if self.type else None,
            "order": self.order,
        }

class TripAddress(db.Model):
    __tablename__ = "trip_addresses"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), nullable=False)

    # Relationships
    trip = db.relationship("Trip", back_populates="addresses")
    address = db.relationship("Address", back_populates="trips")

    def __repr__(self):
        return f"<TripAddress(trip_id={self.trip_id}, address_id={self.address_id})>"

    def to_dict(self, include_address: bool = True):
        """
        Serializable dict for TripAddress.
        include_address: if True, include nested address.to_dict()
        """
        base = {
            "id": self.id,
            "trip_id": self.trip_id,
            "address_id": self.address_id,
        }
        if include_address and self.address:
            # include minimal address representation
            base["address"] = self.address.to_dict()
        else:
            base["address"] = None
        return base
