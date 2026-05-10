from app import db
from datetime import datetime


class Violation(db.Model):
    __tablename__ = 'violations'

    violation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.res_id'), nullable=False)
    reason = db.Column(db.String(100), nullable=True)
    penalty = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    reservation = db.relationship('Reservation', backref='violations')

    def to_dict(self):
        return {
            'violation_id': self.violation_id,
            'user_id': self.user_id,
            'reservation_id': self.reservation_id,
            'reason': self.reason,
            'penalty': self.penalty,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }