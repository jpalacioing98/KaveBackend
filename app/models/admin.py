


from app.models.user import User, admin_driver
from app import db

class Admin(User):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    permissions = db.Column(db.JSON, default=lambda: ['read', 'write'])
    created_by = db.Column(db.Integer, db.ForeignKey('superusers.id'), nullable=True)
    
    assigned_drivers = db.relationship(
        'Driver',
        secondary=admin_driver,
        backref=db.backref('assigned_admins', lazy='dynamic'),
        lazy='dynamic'
    )
    
    __mapper_args__ = {'polymorphic_identity': 'admin'}
    
    def to_dict(self, include_drivers=False):
        data = super().to_dict()
        data.update({
            'full_name': self.full_name,
            'phone': self.phone,
            'permissions': self.permissions,
            'created_by': self.created_by
        })
        if include_drivers:
            data['assigned_drivers_count'] = self.assigned_drivers.count()
        return data