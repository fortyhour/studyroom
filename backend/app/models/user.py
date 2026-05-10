from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    credit_score = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_del = db.Column(db.Integer, default=0)

    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))
    reservations = db.relationship('Reservation', backref='user', lazy='dynamic')
    violations = db.relationship('Violation', backref='user', lazy='dynamic')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'credit_score': self.credit_score,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'is_del': self.is_del,
            'roles': [role.role_name for role in self.roles]
        }


class UserRole(db.Model):
    __tablename__ = 'user_roles'

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), primary_key=True)