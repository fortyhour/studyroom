from app import db
from datetime import datetime


class RoomCheckInCode(db.Model):
    __tablename__ = 'room_checkin_codes'

    code_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.Integer, db.ForeignKey('studyrooms.room_id'), nullable=False)
    code_date = db.Column(db.Date, nullable=False)
    checkin_code = db.Column(db.String(10), nullable=False)
    qr_code_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'code_id': self.code_id,
            'room_id': self.room_id,
            'code_date': self.code_date.strftime('%Y-%m-%d') if self.code_date else None,
            'checkin_code': self.checkin_code,
            'qr_code_url': self.qr_code_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }