from flask import Blueprint, jsonify
from app.models.reservation import Reservation
from app.models.violation import Violation
from app.models.studyroom import StudyRoom
from app.models.seat import Seat
from app import db
from app.utils.decorators import admin_required
from datetime import datetime, date

statistics_bp = Blueprint('statistics', __name__)


# ============================================================
# GET /api/v1/statistics/overview
# 功能: 获取管理端仪表盘统计概览
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# 返回:
#   {
#     "today_reservations": 25,       // 今日预约总数
#     "today_violations": 3,          // 今日违约数
#     "room_stats": [                 // 各自习室统计
#       { "room_id":1, "room_name":"A", "total_seats":50,
#         "occupied_seats":20, "occupancy_rate":40.0 },
#       ...
#     ]
#   }
# ============================================================
@statistics_bp.route('/overview', methods=['GET'])
@admin_required
def overview():
    today = date.today()

    total_reservations_today = Reservation.query.filter(
        Reservation.is_del == 0,
        db.func.date(Reservation.created_at) == today
    ).count()

    total_violations_today = Violation.query.filter(
        db.func.date(Violation.created_at) == today
    ).count()

    rooms = StudyRoom.query.filter_by(is_del=0).all()
    room_stats = []
    for room in rooms:
        total_seats = Seat.query.filter_by(room_id=room.room_id, is_del=0, is_active=True).count()
        now = datetime.now()
        occupied = Reservation.query.filter(
            Reservation.seat_id.in_(
                db.session.query(Seat.seat_id).filter(Seat.room_id == room.room_id, Seat.is_del == 0)
            ),
            Reservation.status.in_(['PENDING', 'ACTIVE']),
            Reservation.start_time <= now,
            Reservation.end_time >= now,
            Reservation.is_del == 0
        ).count()

        room_stats.append({
            'room_id': room.room_id,
            'room_name': room.room_name,
            'total_seats': total_seats,
            'occupied_seats': occupied,
            'occupancy_rate': round(occupied / total_seats * 100, 1) if total_seats > 0 else 0
        })

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'today_reservations': total_reservations_today,
            'today_violations': total_violations_today,
            'room_stats': room_stats
        }
    })