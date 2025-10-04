


from app.models.user import User
from app import db

class SuperUser(User):
    __tablename__ = 'superusers'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    __mapper_args__ = {'polymorphic_identity': 'superuser'}
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'full_name': self.full_name,
            'phone': self.phone
        })
        return data