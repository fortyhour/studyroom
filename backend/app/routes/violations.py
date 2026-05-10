from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.violation import Violation
from app.models.user import User
from app.models.reservation import Reservation
from app.models.seat import Seat
from app.models.studyroom import StudyRoom

violations_bp = Blueprint('violations', __name__)


# ============================================================
# GET /api/v1/violations
# 功能: 获取违约记录列表（分页）
# 权限: 需登录（JWT Token）
#       - 学生只能查看自己的违约记录
#       - 管理员/超级管理员可查看所有用户的违约记录
# 请求头: Authorization: Bearer <access_token>
# Query 参数:
#   ?user_id=    // 选填，按用户ID筛选（仅管理员有效）
#   &page=1      // 页码，默认1
#   &size=10     // 每页条数，默认10
# 返回: 分页违约列表，含用户名、自习室、座位号、预约时间等扩展信息
# ============================================================
@violations_bp.route('', methods=['GET'])
@jwt_required()
def violation_list():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    filter_user_id = request.args.get('user_id', type=int)

    user = User.query.get(int(user_id))
    is_admin = any(role.role_name in ['管理员', '超级管理员'] for role in user.roles) if user else False

    query = Violation.query
    if not is_admin:
        query = query.filter(Violation.user_id == int(user_id))
    elif filter_user_id:
        query = query.filter(Violation.user_id == filter_user_id)

    pagination = query.order_by(Violation.created_at.desc()).paginate(
        page=page, per_page=size, error_out=False
    )

    result = []
    for v in pagination.items:
        item = v.to_dict()
        violator = User.query.get(v.user_id)
        if violator:
            item['username'] = violator.username

        reservation = Reservation.query.get(v.reservation_id)
        if reservation:
            item['start_time'] = reservation.start_time.strftime('%Y-%m-%d %H:%M:%S') if reservation.start_time else None
            item['end_time'] = reservation.end_time.strftime('%Y-%m-%d %H:%M:%S') if reservation.end_time else None
            seat = Seat.query.get(reservation.seat_id)
            if seat:
                item['seat_number'] = seat.seat_number
                room = StudyRoom.query.get(seat.room_id)
                if room:
                    item['room_name'] = room.room_name

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