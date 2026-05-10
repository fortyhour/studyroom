from app import db


class StudyRoom(db.Model):
    __tablename__ = 'studyrooms'

    room_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    total_seats = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    is_del = db.Column(db.Integer, default=0)

    seats = db.relationship('Seat', backref='studyroom', lazy='dynamic')
    checkin_codes = db.relationship('RoomCheckInCode', backref='studyroom', lazy='dynamic')

    def to_dict(self):
        return {
            'room_id': self.room_id,
            'room_name': self.room_name,
            'location': self.location,
            'open_time': self.open_time.strftime('%H:%M') if self.open_time else None,
            'close_time': self.close_time.strftime('%H:%M') if self.close_time else None,
            'is_available': self.is_available,
            'total_seats': self.total_seats,
            'description': self.description,
            'is_del': self.is_del
        }