


from app.models.user import User
from app import db

class Traveler(User):
    __tablename__ = 'travelers'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    dni = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    emergency_contact = db.Column(db.JSON, nullable=True)

    total_trips = db.Column(db.Integer, default=0)
    
    __mapper_args__ = {'polymorphic_identity': 'traveler'}
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'full_name': self.full_name,
            'dni': self.dni,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'emergency_contact': self.emergency_contact,
            'total_trips': self.total_trips
        })
        return data