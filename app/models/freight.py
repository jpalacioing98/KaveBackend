from datetime import datetime
from app import db

class Freight(db.Model):
    __tablename__ = 'freights'

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    description = db.Column(db.String(255))
    origin = db.Column(db.String(100))
    destination = db.Column(db.String(100))
    weight = db.Column(db.Float)
    status = db.Column(db.String(50), default='Pendiente')  # Pendiente, Aceptado, En tránsito, Entregado, Rechazado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    driver = db.relationship('Driver', backref='freights')

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'origin': self.origin,
            'destination': self.destination,
            'weight': self.weight,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
