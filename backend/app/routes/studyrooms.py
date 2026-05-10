from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.studyroom import StudyRoom
from app.models.seat import Seat
from app.models.reservation import Reservation
from app import db
from app.utils.decorators import admin_required
from datetime import datetime

studyrooms_bp = Blueprint('studyrooms', __name__)


# ============================================================
# GET /api/v1/studyrooms
# 功能: 获取自习室列表（分页、筛选），含实时空闲座位统计
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# Query 参数:
#   ?available=true    // 选填，按是否可用筛选
#   &location=         // 选填，按位置模糊搜索
#   &has_power=true    // 选填，按是否有插座筛选（暂未对自习室直接过滤）
#   &page=1            // 页码，默认1
#   &size=10           // 每页条数，默认10
# 返回: 分页自习室列表，每项含 total_seats/occupied_seats/free_seats
# ============================================================
@studyrooms_bp.route('', methods=['GET'])
@jwt_required()
def studyroom_list():
    available = request.args.get('available', type=bool)
    location = request.args.get('location', '')
    has_power = request.args.get('has_power', type=bool)
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)

    query = StudyRoom.query.filter(StudyRoom.is_del == 0)

    if available is not None:
        query = query.filter(StudyRoom.is_available == available)
    if location:
        query = query.filter(StudyRoom.location.contains(location))

    pagination = query.order_by(StudyRoom.room_id).paginate(page=page, per_page=size, error_out=False)

    result = []
    now = datetime.now()
    today = now.date()
    for room in pagination.items:
        room_data = room.to_dict()
        total_seats = Seat.query.filter_by(room_id=room.room_id, is_del=0).count()
        active_seats = Seat.query.filter_by(room_id=room.room_id, is_del=0, is_active=True).count()
        inactive_seats = total_seats - active_seats
        occupied = Reservation.query.filter(
            Reservation.seat_id.in_(
                db.session.query(Seat.seat_id).filter(Seat.room_id == room.room_id, Seat.is_del == 0)
            ),
            Reservation.status.in_(['PENDING', 'ACTIVE']),
            Reservation.start_time <= now,
            Reservation.end_time >= now,
            Reservation.is_del == 0
        ).count()
        room_data['total_seats'] = total_seats
        room_data['occupied_seats'] = occupied
        room_data['free_seats'] = total_seats - inactive_seats - occupied
        result.append(room_data)

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
# POST /api/v1/studyrooms
# 功能: 创建新自习室
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# 请求体 JSON:
#   {
#     "room_name": "自习室A",    // 必填，自习室名称
#     "location": "教学楼1层",    // 选填，位置描述
#     "open_time": "07:00",       // 选填，开放时间，默认07:00
#     "close_time": "22:00",      // 选填，关闭时间，默认22:00
#     "description": "安静区域"    // 选填，备注
#   }
# 返回: 创建的自习室信息
# ============================================================
@studyrooms_bp.route('', methods=['POST'])
@admin_required
def create_studyroom():
    data = request.get_json()

    try:
        open_time = datetime.strptime(data.get('open_time', '07:00'), '%H:%M').time()
        close_time = datetime.strptime(data.get('close_time', '22:00'), '%H:%M').time()
    except ValueError:
        return jsonify({'code': 400, 'message': '时间格式错误', 'data': None}), 400

    room = StudyRoom(
        room_name=data.get('room_name'),
        location=data.get('location', ''),
        open_time=open_time,
        close_time=close_time,
        description=data.get('description', ''),
        is_available=True
    )
    db.session.add(room)
    db.session.commit()

    return jsonify({'code': 200, 'message': '创建成功', 'data': room.to_dict()})


# ============================================================
# GET /api/v1/studyrooms/{room_id}
# 功能: 获取自习室详情，含座位列表及占用状态
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# URL 参数: room_id - 自习室ID
# 返回: 自习室信息 + seats座位数组（每项含is_occupied）+ free_seats/total_seats
# ============================================================
@studyrooms_bp.route('/<int:room_id>', methods=['GET'])
@jwt_required()
def studyroom_detail(room_id):
    room = StudyRoom.query.get(room_id)
    if not room or room.is_del:
        return jsonify({'code': 404, 'message': '自习室不存在', 'data': None}), 404

    room_data = room.to_dict()
    seats = Seat.query.filter_by(room_id=room_id, is_del=0).all()
    now = datetime.now()
    seat_data = []
    for seat in seats:
        active_res = None
        if seat.is_active:
            active_res = Reservation.query.filter(
                Reservation.seat_id == seat.seat_id,
                Reservation.status.in_(['PENDING', 'ACTIVE']),
                Reservation.start_time <= now,
                Reservation.end_time >= now,
                Reservation.is_del == 0
            ).first()
        sd = seat.to_dict()
        sd['is_occupied'] = active_res is not None
        seat_data.append(sd)

    room_data['seats'] = seat_data
    total_seats = len(seat_data)
    inactive_seats = sum(1 for s in seat_data if not s.get('is_active', True))
    occupied_seats = sum(1 for s in seat_data if s['is_occupied'])
    room_data['free_seats'] = total_seats - inactive_seats - occupied_seats
    room_data['total_seats'] = total_seats

    return jsonify({'code': 200, 'message': 'success', 'data': room_data})


# ============================================================
# PUT /api/v1/studyrooms/{room_id}
# 功能: 更新自习室信息
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: room_id - 自习室ID
# 请求体 JSON:
#   {
#     "room_name": "新名称",      // 选填
#     "location": "新位置",       // 选填
#     "open_time": "08:00",       // 选填，格式 HH:MM
#     "close_time": "21:00",      // 选填，格式 HH:MM
#     "is_available": false,      // 选填，是否开放
#     "description": "新描述"      // 选填
#   }
# 返回: 更新后的自习室信息
# ============================================================
@studyrooms_bp.route('/<int:room_id>', methods=['PUT'])
@admin_required
def update_studyroom(room_id):
    room = StudyRoom.query.get(room_id)
    if not room or room.is_del:
        return jsonify({'code': 404, 'message': '自习室不存在', 'data': None}), 404

    data = request.get_json()
    if 'room_name' in data:
        room.room_name = data['room_name']
    if 'location' in data:
        room.location = data['location']
    if 'open_time' in data:
        room.open_time = datetime.strptime(data['open_time'], '%H:%M').time()
    if 'close_time' in data:
        room.close_time = datetime.strptime(data['close_time'], '%H:%M').time()
    if 'is_available' in data:
        room.is_available = data['is_available']
    if 'description' in data:
        room.description = data['description']

    db.session.commit()

    return jsonify({'code': 200, 'message': '更新成功', 'data': room.to_dict()})


# ============================================================
# DELETE /api/v1/studyrooms/{room_id}
# 功能: 删除自习室（软删除）
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: room_id - 自习室ID
# 返回: 操作结果
# ============================================================
@studyrooms_bp.route('/<int:room_id>', methods=['DELETE'])
@admin_required
def delete_studyroom(room_id):
    room = StudyRoom.query.get(room_id)
    if not room or room.is_del:
        return jsonify({'code': 404, 'message': '自习室不存在', 'data': None}), 404

    room.is_del = 1
    db.session.commit()

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


# ============================================================
# GET /api/v1/studyrooms/{room_id}/availability-summary
# 功能: 获取自习室今日空闲座位概况（学生首页用）
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# URL 参数: room_id - 自习室ID
# 返回: { room_id, room_name, total_seats, occupied_seats, free_seats }
# ============================================================
@studyrooms_bp.route('/<int:room_id>/availability-summary', methods=['GET'])
@jwt_required()
def availability_summary(room_id):
    room = StudyRoom.query.get(room_id)
    if not room or room.is_del:
        return jsonify({'code': 404, 'message': '自习室不存在', 'data': None}), 404

    total_seats = Seat.query.filter_by(room_id=room_id, is_del=0, is_active=True).count()
    now = datetime.now()
    occupied = Reservation.query.filter(
        Reservation.seat_id.in_(
            db.session.query(Seat.seat_id).filter(Seat.room_id == room_id, Seat.is_del == 0)
        ),
        Reservation.status.in_(['PENDING', 'ACTIVE']),
        Reservation.start_time <= now,
        Reservation.end_time >= now,
        Reservation.is_del == 0
    ).count()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'room_id': room_id,
            'room_name': room.room_name,
            'total_seats': total_seats,
            'occupied_seats': occupied,
            'free_seats': total_seats - occupied
        }
    })