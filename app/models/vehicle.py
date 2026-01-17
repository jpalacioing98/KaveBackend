from app import db


class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)        # marca
    model = db.Column(db.String(50), nullable=False)       # modelo
    year = db.Column(db.Integer, nullable=False)           # año
    color = db.Column(db.String(30), nullable=True)        # color
    plate = db.Column(db.String(20), unique=True, nullable=False)  # placa
    seats = db.Column(db.Integer, nullable=False, default=4)       # cupos

    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id', ondelete='CASCADE'),
                          nullable=False, unique=True)

    driver = db.relationship('Driver', back_populates='vehicle')

    def to_dict(self):
        return {
            'id': self.id,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'color': self.color,
            'plate': self.plate,
            'seats': self.seats,
            'driver_id': self.driver_id
        }

    def __repr__(self):
        return f"<Vehicle(id={self.id}, plate='{self.plate}', driver_id={self.driver_id})>"
