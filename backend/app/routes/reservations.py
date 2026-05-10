from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.reservation import Reservation
from app.models.seat import Seat
from app.models.studyroom import StudyRoom
from app.models.system_config import SystemConfig
from app.models.user import User
from app import db
from app.utils.decorators import admin_required
from datetime import datetime, date, timedelta

reservations_bp = Blueprint('reservations', __name__)


# ============================================================
# POST /api/v1/reservations
# 功能: 创建预约
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# 请求体 JSON:
#   {
#     "seat_id": 5,                              // 必填，座位ID
#     "start_time": "2026-05-10 09:00:00",       // 必填，开始时间（整点）
#     "end_time": "2026-05-10 11:00:00"          // 必填，结束时间（整点）
#   }
# 校验:
#   - 时间必须为整点
#   - 时长 ≤ MAX_RESERVATION_HOURS（系统配置）
#   - 不能超出自习室开放时间
#   - 不能与其他预约冲突
#   - 用户信誉分必须大于0（credit_score > 0）
#   - 日期范围从今天起 MAX_RESERVATION_DAYS 天内（默认7天）
# 返回: 创建的预约信息，状态 PENDING
# ============================================================
@reservations_bp.route('', methods=['POST'])
@jwt_required()
def create_reservation():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    seat_id = data.get('seat_id')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    if not all([seat_id, start_time_str, end_time_str]):
        return jsonify({'code': 400, 'message': '参数不完整', 'data': None}), 400

    try:
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'code': 400, 'message': '时间格式错误', 'data': None}), 400

    if start_time.minute != 0 or end_time.minute != 0:
        return jsonify({'code': 400, 'message': '预约时间必须为整点', 'data': None}), 400

    max_days_config = SystemConfig.query.filter_by(config_key='MAX_RESERVATION_DAYS').first()
    max_days = int(max_days_config.config_value) if max_days_config else 7
    today = date.today()
    if start_time.date() < today:
        return jsonify({'code': 400, 'message': '不能预约过去的日期', 'data': None}), 400
    if start_time.date() > today + timedelta(days=max_days):
        return jsonify({'code': 400, 'message': f'只能预约{max_days}天内的日期', 'data': None}), 400

    max_hours_config = SystemConfig.query.filter_by(config_key='MAX_RESERVATION_HOURS').first()
    max_hours = int(max_hours_config.config_value) if max_hours_config else 4

    duration = (end_time - start_time).total_seconds() / 3600
    if duration <= 0 or duration > max_hours:
        return jsonify({'code': 400, 'message': f'预约时长需在1-{max_hours}小时之间', 'data': None}), 400

    seat = Seat.query.get(seat_id)
    if not seat or seat.is_del or not seat.is_active:
        return jsonify({'code': 400, 'message': '座位不可用', 'data': None}), 400

    room = StudyRoom.query.get(seat.room_id)
    if not room:
        return jsonify({'code': 400, 'message': '自习室不存在', 'data': None}), 400

    start_hour = start_time.hour
    end_hour = end_time.hour
    if start_hour < room.open_time.hour or end_hour > room.close_time.hour:
        return jsonify({'code': 400, 'message': '预约时间超出自习室开放时间', 'data': None}), 400

    conflicting = Reservation.query.filter(
        Reservation.seat_id == seat_id,
        Reservation.status.in_(['PENDING', 'ACTIVE']),
        Reservation.is_del == 0,
        Reservation.start_time < end_time,
        Reservation.end_time > start_time
    ).first()

    if conflicting:
        return jsonify({'code': 400, 'message': '该时间段已被预约', 'data': None}), 400

    user_cross_seat_conflict = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.seat_id != seat_id,
        Reservation.status.in_(['PENDING', 'ACTIVE']),
        Reservation.is_del == 0,
        Reservation.start_time < end_time,
        Reservation.end_time > start_time
    ).first()

    if user_cross_seat_conflict:
        return jsonify({'code': 400, 'message': '该时间段你已预约了其他座位', 'data': None}), 400

    same_day_count = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.status.in_(['PENDING', 'ACTIVE']),
        Reservation.is_del == 0,
        db.func.date(Reservation.start_time) == start_time.date()
    ).count()

    if same_day_count >= 2:
        return jsonify({'code': 400, 'message': '同一天最多只能预约2次', 'data': None}), 400

    user = User.query.get(user_id)
    if not user or user.is_del:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404

    if user.credit_score <= 0:
        return jsonify({'code': 400, 'message': '信誉分不足，无法预约', 'data': None}), 400

    reservation = Reservation(
        user_id=user_id,
        seat_id=seat_id,
        start_time=start_time,
        end_time=end_time,
        status='PENDING'
    )
    db.session.add(reservation)
    db.session.commit()

    return jsonify({'code': 200, 'message': '预约成功', 'data': reservation.to_dict()})


# ============================================================
# GET /api/v1/reservations/my
# 功能: 获取当前用户的预约列表（分页、状态筛选）
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# Query 参数:
#   ?status=PENDING   // 选填，按状态筛选，支持逗号分隔多值如 PENDING,ACTIVE
#   &page=1           // 页码，默认1
#   &size=10          // 每页条数，默认10
# 返回: 分页预约列表，含自习室名称、座位号、插座等扩展信息
# ============================================================
@reservations_bp.route('/my', methods=['GET'])
@jwt_required()
def my_reservations():
    user_id = int(get_jwt_identity())
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)

    query = Reservation.query.filter_by(user_id=user_id, is_del=0)
    if status:
        status_list = [s.strip() for s in status.split(',') if s.strip()]
        if len(status_list) == 1:
            query = query.filter(Reservation.status == status_list[0])
        else:
            query = query.filter(Reservation.status.in_(status_list))

    pagination = query.order_by(Reservation.created_at.desc()).paginate(page=page, per_page=size, error_out=False)

    result = []
    for r in pagination.items:
        item = r.to_dict()
        seat = Seat.query.get(r.seat_id)
        if seat:
            item['seat_number'] = seat.seat_number
            item['has_power'] = seat.has_power
            room = StudyRoom.query.get(seat.room_id)
            if room:
                item['room_name'] = room.room_name
                item['location'] = room.location
        result.append(item)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': result,
            'total': pagination.total,
            'page': page,
            'size': size,
            'pages': pagination.pages
        }
    })


# ============================================================
# GET /api/v1/reservations/{res_id}
# 功能: 获取单条预约详情
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# URL 参数: res_id - 预约ID
# 返回: 预约完整信息，含自习室名称、座位号、位置、插座等
# ============================================================
@reservations_bp.route('/<int:res_id>', methods=['GET'])
@jwt_required()
def reservation_detail(res_id):
    reservation = Reservation.query.get(res_id)
    if not reservation or reservation.is_del:
        return jsonify({'code': 404, 'message': '预约记录不存在', 'data': None}), 404

    item = reservation.to_dict()
    seat = Seat.query.get(reservation.seat_id)
    if seat:
        item['seat_number'] = seat.seat_number
        item['has_power'] = seat.has_power
        room = StudyRoom.query.get(seat.room_id)
        if room:
            item['room_name'] = room.room_name
            item['location'] = room.location

    return jsonify({'code': 200, 'message': 'success', 'data': item})


# ============================================================
# PUT /api/v1/reservations/{res_id}/cancel
# 功能: 取消预约
# 权限: 需登录（JWT Token）
#       - 本人只能取消自己的 PENDING 状态预约
#       - 管理员/超级管理员可以取消任意用户的 PENDING 状态预约
# 请求头: Authorization: Bearer <access_token>
# URL 参数: res_id - 预约ID
# 限制: 仅 PENDING 状态可取消
# 返回: 取消后的预约信息，状态变为 CANCELLED
# ============================================================
@reservations_bp.route('/<int:res_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_reservation(res_id):
    user_id = int(get_jwt_identity())
    reservation = Reservation.query.get(res_id)

    if not reservation or reservation.is_del:
        return jsonify({'code': 404, 'message': '预约记录不存在', 'data': None}), 404

    if reservation.status != 'PENDING':
        return jsonify({'code': 400, 'message': '只能取消待签到状态的预约', 'data': None}), 400

    if reservation.user_id != user_id:
        from app.utils.decorators import admin_required as admin_check
        user = __import__('app.models.user', fromlist=['User']).User.query.get(user_id)
        if not user:
            return jsonify({'code': 403, 'message': '无权限取消此预约', 'data': None}), 403
        is_admin = any(role.role_name in ['管理员', '超级管理员'] for role in user.roles)
        if not is_admin:
            return jsonify({'code': 403, 'message': '无权限取消此预约', 'data': None}), 403

    reservation.status = 'CANCELLED'
    db.session.commit()

    return jsonify({'code': 200, 'message': '取消成功', 'data': reservation.to_dict()})


# ============================================================
# POST /api/v1/reservations/{res_id}/checkin
# 功能: 签到
# 权限: 需登录（JWT Token），仅本人可签到自己的预约
# 请求头: Authorization: Bearer <access_token>
# URL 参数: res_id - 预约ID
# 请求体 JSON:
#   { "checkin_code": "A1B2C3" }   // 必填，6位签到码
# 校验:
#   - 预约状态必须为 PENDING
#   - 签到码必须与座位所属自习室当日的签到码一致
# 注: 签到成功后信誉分 +5（不超过100）
# 返回: 签到后的预约信息，状态变为 ACTIVE
# ============================================================
@reservations_bp.route('/<int:res_id>/checkin', methods=['POST'])
@jwt_required()
def checkin(res_id):
    user_id = int(get_jwt_identity())
    reservation = Reservation.query.get(res_id)

    if not reservation or reservation.is_del:
        return jsonify({'code': 404, 'message': '预约记录不存在', 'data': None}), 404

    if reservation.user_id != user_id:
        return jsonify({'code': 403, 'message': '只能签到自己的预约', 'data': None}), 403

    if reservation.status != 'PENDING':
        return jsonify({'code': 400, 'message': '只能签到待签到状态的预约', 'data': None}), 400

    data = request.get_json()
    checkin_code = data.get('checkin_code', '')

    seat = Seat.query.get(reservation.seat_id)
    if not seat:
        return jsonify({'code': 400, 'message': '座位不存在', 'data': None}), 400

    from app.models.checkin_code import RoomCheckInCode
    today = date.today()
    room_code = RoomCheckInCode.query.filter_by(
        room_id=seat.room_id,
        code_date=today
    ).first()

    if not room_code:
        return jsonify({'code': 400, 'message': '今日签到码未生成', 'data': None}), 400

    if room_code.checkin_code != checkin_code:
        return jsonify({'code': 400, 'message': '签到码错误', 'data': None}), 400

    now = datetime.now()
    reservation.actual_check_in = now
    reservation.status = 'ACTIVE'

    user = User.query.get(user_id)
    if user:
        user.credit_score = min(100, user.credit_score + 5)

    db.session.commit()

    return jsonify({'code': 200, 'message': '签到成功', 'data': reservation.to_dict()})


# ============================================================
# PUT /api/v1/reservations/{res_id}/complete
# 功能: 提前结束本次使用（ACTIVE -> COMPLETED）
# 权限: 需登录（JWT Token），仅本人可结束自己的预约
# 请求头: Authorization: Bearer <access_token>
# URL 参数: res_id - 预约ID
# 校验: 预约状态必须为 ACTIVE
# 返回: 更新后的预约信息，状态变为 COMPLETED，actual_end_time 为当前时间
# ============================================================
@reservations_bp.route('/<int:res_id>/complete', methods=['PUT'])
@jwt_required()
def complete_reservation(res_id):
    user_id = int(get_jwt_identity())
    reservation = Reservation.query.get(res_id)

    if not reservation or reservation.is_del:
        return jsonify({'code': 404, 'message': '预约记录不存在', 'data': None}), 404

    if reservation.user_id != user_id:
        return jsonify({'code': 403, 'message': '只能结束自己的预约', 'data': None}), 403

    if reservation.status != 'ACTIVE':
        return jsonify({'code': 400, 'message': '只能结束进行中的预约', 'data': None}), 400

    reservation.status = 'COMPLETED'
    reservation.actual_check_in = datetime.now()
    db.session.commit()

    return jsonify({'code': 200, 'message': '已提前结束使用', 'data': reservation.to_dict()})


# ============================================================
# GET /api/v1/reservations/admin/reservations
# 功能: 管理端查询所有预约记录（分页、多条件筛选）
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# Query 参数:
#   ?user_id=       // 选填，按用户ID筛选
#   &status=        // 选填，按状态筛选
#   &room_id=       // 选填，按自习室ID筛选
#   &start_date=    // 选填，开始日期
#   &end_date=      // 选填，结束日期
#   &page=1         // 页码，默认1
#   &size=10        // 每页条数，默认10
# 返回: 分页预约列表，含用户名、邮箱、自习室等扩展信息
# ============================================================
@reservations_bp.route('/admin/reservations', methods=['GET'])
@admin_required
def admin_reservations():
    user_id = request.args.get('user_id', type=int)
    status = request.args.get('status', '')
    room_id = request.args.get('room_id', type=int)
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)

    query = Reservation.query.filter(Reservation.is_del == 0)

    if user_id:
        query = query.filter(Reservation.user_id == user_id)
    if status:
        query = query.filter(Reservation.status == status)
    if room_id:
        seat_ids = db.session.query(Seat.seat_id).filter(Seat.room_id == room_id).subquery()
        query = query.filter(Reservation.seat_id.in_(seat_ids))

    pagination = query.order_by(Reservation.created_at.desc()).paginate(page=page, per_page=size, error_out=False)

    result = []
    for r in pagination.items:
        item = r.to_dict()
        seat = Seat.query.get(r.seat_id)
        if seat:
            item['seat_number'] = seat.seat_number
            room = StudyRoom.query.get(seat.room_id)
            if room:
                item['room_name'] = room.room_name
                item['location'] = room.location
        from app.models.user import User
        u = User.query.get(r.user_id)
        if u:
            item['username'] = u.username
            item['email'] = u.email
        result.append(item)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': result,
            'total': pagination.total,
            'page': page,
            'size': size,
            'pages': pagination.pages
        }
    })