from app import db
from datetime import datetime

class WhatsAppUser(db.Model):
    __tablename__ = "whatsapp_users"

    id = db.Column(db.Integer, primary_key=True)

    phone = db.Column(db.String(20), unique=True, nullable=False)

    traveler_id = db.Column(
        db.Integer,
        db.ForeignKey("travelers.id"),
        nullable=True
    )

    flow = db.Column(db.String(50), nullable=True)
    step = db.Column(db.String(50), nullable=True)

    temp_data = db.Column(db.JSON, nullable=True)  # datos temporales del flujo

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    traveler = db.relationship("Traveler", backref="whatsapp_user", uselist=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "phone": self.phone,
            "traveler_id": self.traveler_id,
            "flow": self.flow,
            "step": self.step,
            "temp_data": self.temp_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }