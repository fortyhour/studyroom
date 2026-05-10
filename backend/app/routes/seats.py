from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.seat import Seat
from app.models.reservation import Reservation
from app.models.studyroom import StudyRoom
from app.models.system_config import SystemConfig
from app import db
from app.utils.decorators import admin_required
from datetime import datetime, timedelta, date

seats_bp = Blueprint('seats', __name__)


# ============================================================
# GET /api/v1/studyrooms/{room_id}/seats
# 功能: 获取某自习室下的座位列表，含实时占用状态
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# URL 参数: room_id - 自习室ID
# Query 参数:
#   ?has_power=true   // 选填，筛选是否有插座
#   &is_active=true   // 选填，筛选是否可用
# 返回: 座位数组，每项含 is_occupied 标记当前是否被占用
# ============================================================
@seats_bp.route('/studyrooms/<int:room_id>/seats', methods=['GET'])
@jwt_required()
def seat_list(room_id):
    has_power = request.args.get('has_power', type=bool)
    is_active = request.args.get('is_active', type=bool)

    query = Seat.query.filter_by(room_id=room_id, is_del=0)

    if has_power is not None:
        query = query.filter(Seat.has_power == has_power)
    if is_active is not None:
        query = query.filter(Seat.is_active == is_active)

    seats = query.order_by(Seat.seat_number).all()
    now = datetime.now()
    result = []
    for seat in seats:
        active_res = Reservation.query.filter(
            Reservation.seat_id == seat.seat_id,
            Reservation.status.in_(['PENDING', 'ACTIVE']),
            Reservation.start_time <= now,
            Reservation.end_time >= now,
            Reservation.is_del == 0
        ).first()
        sd = seat.to_dict()
        sd['is_occupied'] = active_res is not None
        result.append(sd)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': result
    })


# ============================================================
# POST /api/v1/studyrooms/{room_id}/seats
# 功能: 在某自习室下新增座位
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: room_id - 自习室ID
# 请求体 JSON:
#   {
#     "seat_number": 10,    // 必填，座位编号（同一自习室内应唯一）
#     "has_power": false    // 选填，是否有插座，默认false
#   }
# 返回: 创建的座位信息
# ============================================================
@seats_bp.route('/studyrooms/<int:room_id>/seats', methods=['POST'])
@admin_required
def create_seat(room_id):
    data = request.get_json()
    seat_number = data.get('seat_number', 0)

    existing = Seat.query.filter_by(room_id=room_id, seat_number=seat_number, is_del=0).first()
    if existing:
        return jsonify({'code': 400, 'message': f'该自习室下座位编号 {seat_number} 已存在', 'data': None}), 400

    seat = Seat(
        room_id=room_id,
        seat_number=seat_number,
        has_power=data.get('has_power', False),
        is_active=True
    )
    db.session.add(seat)

    room = StudyRoom.query.get(room_id)
    if room:
        room.total_seats = Seat.query.filter_by(room_id=room_id, is_del=0).count() + 1

    db.session.commit()

    return jsonify({'code': 200, 'message': '创建成功', 'data': seat.to_dict()})


# ============================================================
# GET /api/v1/seats/{seat_id}
# 功能: 获取座位详情
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# URL 参数: seat_id - 座位ID
# 返回: 座位信息
# ============================================================
@seats_bp.route('/seats/<int:seat_id>', methods=['GET'])
@jwt_required()
def seat_detail(seat_id):
    seat = Seat.query.get(seat_id)
    if not seat or seat.is_del:
        return jsonify({'code': 404, 'message': '座位不存在', 'data': None}), 404

    return jsonify({'code': 200, 'message': 'success', 'data': seat.to_dict()})


# ============================================================
# PUT /api/v1/seats/{seat_id}
# 功能: 更新座位信息
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: seat_id - 座位ID
# 请求体 JSON:
#   {
#     "seat_number": 12,   // 选填，座位编号
#     "has_power": true,   // 选填，是否有插座
#     "is_active": false   // 选填，是否可用
#   }
# 返回: 更新后的座位信息
# ============================================================
@seats_bp.route('/seats/<int:seat_id>', methods=['PUT'])
@admin_required
def update_seat(seat_id):
    seat = Seat.query.get(seat_id)
    if not seat or seat.is_del:
        return jsonify({'code': 404, 'message': '座位不存在', 'data': None}), 404

    data = request.get_json()
    if 'seat_number' in data:
        new_number = data['seat_number']
        conflicting = Seat.query.filter(
            Seat.room_id == seat.room_id,
            Seat.seat_number == new_number,
            Seat.seat_id != seat_id,
            Seat.is_del == 0
        ).first()
        if conflicting:
            return jsonify({'code': 400, 'message': f'该自习室下座位编号 {new_number} 已存在', 'data': None}), 400
        seat.seat_number = new_number
    if 'has_power' in data:
        seat.has_power = data['has_power']
    if 'is_active' in data:
        seat.is_active = data['is_active']

    db.session.commit()

    return jsonify({'code': 200, 'message': '更新成功', 'data': seat.to_dict()})


# ============================================================
# DELETE /api/v1/seats/{seat_id}
# 功能: 删除座位（软删除）
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: seat_id - 座位ID
# 返回: 操作结果
# ============================================================
@seats_bp.route('/seats/<int:seat_id>', methods=['DELETE'])
@admin_required
def delete_seat(seat_id):
    seat = Seat.query.get(seat_id)
    if not seat or seat.is_del:
        return jsonify({'code': 404, 'message': '座位不存在', 'data': None}), 404

    seat.is_del = 1
    room = StudyRoom.query.get(seat.room_id)
    if room:
        room.total_seats = max(0, Seat.query.filter_by(room_id=seat.room_id, is_del=0).count() - 1)

    db.session.commit()

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


# ============================================================
# GET /api/v1/seats/{seat_id}/availability
# 功能: 查询指定座位某日的空闲时间段（整点区间）
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# URL 参数: seat_id - 座位ID
# Query 参数:
#   ?date=2026-05-09   // 选填，日期格式 YYYY-MM-DD，默认当天
# 限制: 日期范围从今天起 MAX_RESERVATION_DAYS 天内（默认7天）
# 返回:
#   {
#     "date": "2026-05-09",
#     "open_time": "07:00",
#     "close_time": "22:00",
#     "slots": [{"start":"07:00","end":"08:00","free":true}, {"start":"08:00","end":"09:00","free":false}, ...]
#   }
# 注: 返回全部整点时段，free=true 为空闲，free=false 为已占用
# ============================================================
@seats_bp.route('/seats/<int:seat_id>/availability', methods=['GET'])
@jwt_required()
def seat_availability(seat_id):
    seat = Seat.query.get(seat_id)
    if not seat or seat.is_del:
        return jsonify({'code': 404, 'message': '座位不存在', 'data': None}), 404

    room = StudyRoom.query.get(seat.room_id)
    if not room:
        return jsonify({'code': 404, 'message': '自习室不存在', 'data': None}), 404

    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'code': 400, 'message': '日期格式错误', 'data': None}), 400

    max_days_config = SystemConfig.query.filter_by(config_key='MAX_RESERVATION_DAYS').first()
    max_days = int(max_days_config.config_value) if max_days_config else 7
    today = date.today()
    if query_date < today:
        return jsonify({'code': 400, 'message': '不能预约过去的日期', 'data': None}), 400
    if query_date > today + timedelta(days=max_days):
        return jsonify({'code': 400, 'message': f'只能预约{max_days}天内的日期', 'data': None}), 400

    open_hour = room.open_time.hour
    close_hour = room.close_time.hour

    existing = Reservation.query.filter(
        Reservation.seat_id == seat_id,
        Reservation.status.in_(['PENDING', 'ACTIVE']),
        Reservation.is_del == 0,
        db.func.date(Reservation.start_time) == query_date
    ).order_by(Reservation.start_time).all()

    all_slots = []
    current = open_hour
    while current < close_hour:
        slot_start = current
        slot_end = current + 1

        is_free = True
        for res in existing:
            res_start_hour = res.start_time.hour + res.start_time.minute / 60.0
            res_end_hour = res.end_time.hour + res.end_time.minute / 60.0
            if not (slot_end <= res_start_hour or slot_start >= res_end_hour):
                is_free = False
                break

        all_slots.append({
            'start': f'{slot_start:02d}:00',
            'end': f'{slot_end:02d}:00',
            'free': is_free
        })

        current += 1

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'date': date_str,
            'open_time': room.open_time.strftime('%H:%M'),
            'close_time': room.close_time.strftime('%H:%M'),
            'slots': all_slots
        }
    })