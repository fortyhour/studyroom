from app import db


class Seat(db.Model):
    __tablename__ = 'seats'

    seat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('studyrooms.room_id'), nullable=False)
    seat_number = db.Column(db.Integer, nullable=False)
    has_power = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_del = db.Column(db.Integer, default=0)

    reservations = db.relationship('Reservation', backref='seat', lazy='dynamic')

    def to_dict(self):
        return {
            'seat_id': self.seat_id,
            'room_id': self.room_id,
            'seat_number': self.seat_number,
            'has_power': self.has_power,
            'is_active': self.is_active,
            'is_del': self.is_del
        }