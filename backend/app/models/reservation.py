from app import db
from datetime import datetime


class Reservation(db.Model):
    __tablename__ = 'reservations'

    res_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.seat_id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='PENDING')
    actual_check_in = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_del = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'res_id': self.res_id,
            'user_id': self.user_id,
            'seat_id': self.seat_id,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'status': self.status,
            'actual_check_in': self.actual_check_in.strftime('%Y-%m-%d %H:%M:%S') if self.actual_check_in else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'is_del': self.is_del
        }