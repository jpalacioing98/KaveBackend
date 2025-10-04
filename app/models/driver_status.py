from datetime import datetime
from app import db

class DriverStatus(db.Model):
    __tablename__ = 'driver_status'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Fuera de servicio')
    location = db.Column(db.String(100), nullable=True)  # Ej: "Valledupar"
    route = db.Column(db.String(120), nullable=True)     # Ej: "Urumita-Valledupar"
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    driver = db.relationship('Driver', backref=db.backref('current_status', uselist=False))

    def to_dict(self):
        return {
            'driver_id': self.driver_id,
            'status': self.status,
            'location': self.location,
            'route': self.route,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
