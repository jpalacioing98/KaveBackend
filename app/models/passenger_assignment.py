from app import db

class PassengerAssignment(db.Model):
    __tablename__ = 'passenger_assignments'

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pickup_location = db.Column(db.String(100))
    dropoff_location = db.Column(db.String(100))
    order = db.Column(db.Integer)  # Orden de recogida
    notified = db.Column(db.Boolean, default=False)

    trip = db.relationship('Trip', back_populates='passengers')
    passenger = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'passenger_id': self.passenger_id,
            'pickup_location': self.pickup_location,
            'dropoff_location': self.dropoff_location,
            'order': self.order,
            'notified': self.notified
        }
