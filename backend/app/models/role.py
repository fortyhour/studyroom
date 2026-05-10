from app import db


class Role(db.Model):
    __tablename__ = 'roles'

    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200), nullable=True)
    is_system = db.Column(db.Boolean, default=False)

    permissions = db.relationship('Permission', secondary='role_permissions', backref=db.backref('roles', lazy='dynamic'))

    def to_dict(self):
        return {
            'role_id': self.role_id,
            'role_name': self.role_name,
            'description': self.description,
            'is_system': self.is_system,
            'permissions': [p.to_dict() for p in self.permissions]
        }

    def to_simple_dict(self):
        return {
            'role_id': self.role_id,
            'role_name': self.role_name,
            'description': self.description,
            'is_system': self.is_system
        }


class RolePermission(db.Model):
    __tablename__ = 'role_permissions'

    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), primary_key=True)
    perm_id = db.Column(db.Integer, db.ForeignKey('permissions.perm_id'), primary_key=True)