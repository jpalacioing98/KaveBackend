
from app import db
from app.models.enums import TripType
from app.models.trip import Trip


class PackageTrip(Trip):
    __tablename__ = "package_trips"

    id = db.Column(db.Integer, db.ForeignKey("trips.id"), primary_key=True)
    title = db.Column(db.String(255), nullable=True,)
    package_description = db.Column(db.String(255), nullable=False)
    weight = db.Column(db.Float, nullable=True)
    dimensions = db.Column(db.String(100), nullable=True)
    pickup_address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), nullable=False)
    delivery_address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), nullable=False)

    pickup_address = db.relationship("Address", foreign_keys=[pickup_address_id])
    delivery_address = db.relationship("Address", foreign_keys=[delivery_address_id])

    __mapper_args__ = {
        "polymorphic_identity": TripType.PACKAGE.value
    }

    def __repr__(self):
        return f"<PackageTrip(id={self.id}, desc='{self.package_description}')>"

    def to_dict(self, include_addresses: bool = True):
        """
        Extend Trip.to_dict() with PackageTrip-specific fields.
        For packages we include explicit pickup/delivery addresses (full dicts).
        """
        data = super().to_dict(include_addresses=include_addresses)
        data.update({
            "title":self.title,
            "package_description": self.package_description,
            "weight": self.weight,
            "dimensions": self.dimensions,
            "pickup_address_id": self.pickup_address_id,
            "delivery_address_id": self.delivery_address_id,
            "pickup_address": self.pickup_address.to_dict() if self.pickup_address else None,
            "delivery_address": self.delivery_address.to_dict() if self.delivery_address else None,
        })
        return data
