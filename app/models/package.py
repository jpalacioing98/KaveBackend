from datetime import datetime
from app import db

class Package(db.Model):
    __tablename__ = 'packages'

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    sender = db.Column(db.String(100))
    recipient = db.Column(db.String(100))
    origin = db.Column(db.String(100))
    destination = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Pendiente')  # Pendiente, Aceptada, En tránsito, Entregada, Rechazada
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    driver = db.relationship('Driver', backref='packages')

    def to_dict(self):
        return {
            'id': self.id,
            'sender': self.sender,
            'recipient': self.recipient,
            'origin': self.origin,
            'destination': self.destination,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
