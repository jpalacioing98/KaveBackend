from app.models.user import User

from app import db


class Driver(User):
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    vehicle_info = db.Column(db.JSON, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    total_trips = db.Column(db.Integer, default=0)
    
    __mapper_args__ = {'polymorphic_identity': 'driver'}
    
    def to_dict(self, include_admins=False):
        data = super().to_dict()
        data.update({
            'full_name': self.full_name,
            'license_number': self.license_number,
            'phone': self.phone,
            'vehicle_info': self.vehicle_info,
            'is_verified': self.is_verified,
            'rating': self.rating,
            'total_trips': self.total_trips
        })
        if include_admins:
            admins = [{'id': admin.id, 'full_name': admin.full_name} 
                     for admin in self.assigned_admins.all()]
            data['assigned_admins'] = admins
        return data
