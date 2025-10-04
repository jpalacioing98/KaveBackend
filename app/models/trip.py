from app import db

class Trip(db.Model):
    __tablename__ = 'trips'

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='Pendiente')  # Pendiente, En curso, Finalizado, Cancelado
    passengers = db.relationship('PassengerAssignment', back_populates='trip', cascade="all, delete-orphan")

    driver = db.relationship('Driver', backref=db.backref('trips', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'driver_id': self.driver_id,
            'origin': self.origin,
            'destination': self.destination,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'passengers': [p.to_dict() for p in self.passengers]
        }
