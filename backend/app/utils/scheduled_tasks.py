from app.models.reservation import Reservation
from app.models.violation import Violation
from app.models.system_config import SystemConfig
from app.models.user import User
from app.models.studyroom import StudyRoom
from app.models.checkin_code import RoomCheckInCode
from app import db
from datetime import datetime, timedelta, date
import random
import string


def check_pending_violations(app):
    with app.app_context():
        now = datetime.now()
        grace_cfg = SystemConfig.query.filter_by(config_key='CHECKIN_GRACE_MINUTES').first()
        checkin_grace = int(grace_cfg.config_value) if grace_cfg else 15
        penalty_cfg = SystemConfig.query.filter_by(config_key='VIOLATION_PENALTY').first()
        penalty = int(penalty_cfg.config_value) if penalty_cfg else 10

        pending_reservations = Reservation.query.filter(
            Reservation.status == 'PENDING',
            Reservation.start_time <= now - timedelta(minutes=checkin_grace),
            Reservation.is_del == 0
        ).all()

        for res in pending_reservations:
            user = User.query.get(res.user_id)
            if user:
                user.credit_score = max(0, user.credit_score - penalty)

            violation = Violation(
                user_id=res.user_id,
                reservation_id=res.res_id,
                reason='超时未签到',
                penalty=penalty
            )
            db.session.add(violation)

            res.status = 'VIOLATED'

        db.session.commit()


def send_reminders(app):
    with app.app_context():
        now = datetime.now()
        before_cfg = SystemConfig.query.filter_by(config_key='REMINDER_BEFORE_MINUTES').first()
        reminder_before = int(before_cfg.config_value) if before_cfg else 15
        second_cfg = SystemConfig.query.filter_by(config_key='SECOND_REMINDER_MINUTES').first()
        second_reminder = int(second_cfg.config_value) if second_cfg else 10

        upcoming = Reservation.query.filter(
            Reservation.status == 'PENDING',
            Reservation.start_time <= now + timedelta(minutes=reminder_before),
            Reservation.start_time >= now,
            Reservation.is_del == 0
        ).all()

        for res in upcoming:
            print(f'[提醒] 用户 {res.user_id} 的预约 {res.res_id} 将在 {res.start_time} 开始')

        overdue = Reservation.query.filter(
            Reservation.status == 'PENDING',
            Reservation.start_time <= now - timedelta(minutes=second_reminder),
            Reservation.start_time >= now - timedelta(minutes=second_reminder + 1),
            Reservation.is_del == 0
        ).all()

        for res in overdue:
            print(f'[再次提醒] 用户 {res.user_id} 的预约 {res.res_id} 已超时未签到')


def generate_daily_checkin_codes(app):
    with app.app_context():
        today = date.today()
        rooms = StudyRoom.query.filter_by(is_del=0).all()

        for room in rooms:
            existing = RoomCheckInCode.query.filter_by(room_id=room.room_id, code_date=today).first()
            if not existing:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                checkin = RoomCheckInCode(
                    room_id=room.room_id,
                    code_date=today,
                    checkin_code=code
                )
                db.session.add(checkin)

        db.session.commit()


def daily_credit_reward(app):
    with app.app_context():
        users = User.query.filter_by(is_del=0).all()
        for user in users:
            if user.credit_score < 100:
                user.credit_score = min(100, user.credit_score + 1)
        db.session.commit()


def register_tasks(scheduler, app):
    scheduler.add_job(
        id='check_violations',
        func=check_pending_violations,
        args=[app],
        trigger='interval',
        minutes=1,
        replace_existing=True
    )
    scheduler.add_job(
        id='send_reminders',
        func=send_reminders,
        args=[app],
        trigger='interval',
        minutes=1,
        replace_existing=True
    )
    scheduler.add_job(
        id='generate_checkin_codes',
        func=generate_daily_checkin_codes,
        args=[app],
        trigger='cron',
        hour=0,
        minute=0,
        replace_existing=True
    )
    scheduler.add_job(
        id='daily_credit_reward',
        func=daily_credit_reward,
        args=[app],
        trigger='cron',
        hour=0,
        minute=0,
        replace_existing=True
    )