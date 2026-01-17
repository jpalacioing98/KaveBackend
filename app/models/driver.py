from app.models.enums import DriverStatus
from app.models.user import User
from app import db


class Driver(User):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum(DriverStatus),
                       default=DriverStatus.AVAILABLE, nullable=False)
    rating = db.Column(db.Float, default=0.0)
    total_trips = db.Column(db.Integer, default=0)

    # Relación uno a uno con Vehicle
    vehicle = db.relationship('Vehicle', back_populates='driver', 
                             uselist=False, cascade='all, delete-orphan')

    __mapper_args__ = {'polymorphic_identity': 'driver'}

    def to_dict(self, include_admins=False):
        data = super().to_dict()
        data.update({
            'full_name': self.full_name,
            'license_number': self.license_number,
            'phone': self.phone,
            'is_verified': self.is_verified,
            'rating': self.rating,
            'total_trips': self.total_trips,
            'status':self.status.value,
            'vehicle': self.vehicle.to_dict() if self.vehicle else None
        })
        if include_admins:
            admins = [{'id': admin.id, 'full_name': admin.full_name}
                      for admin in self.assigned_admins.all()]
            data['assigned_admins'] = admins
        return data

    def __repr__(self):
        return f"<Driver(id={self.id}, name='{self.full_name}', status='{self.status.value}')>"