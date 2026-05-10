from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.checkin_code import RoomCheckInCode
from app.models.studyroom import StudyRoom
from app import db
from datetime import datetime, date
import random
import string

checkin_bp = Blueprint('checkin', __name__)


def _generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# ============================================================
# GET /api/v1/studyrooms/{room_id}/checkin-code
# 功能: 获取某自习室的今日签到码（不存在则自动生成）
# 权限: 需登录（JWT Token），通常管理员或自习室屏幕使用
# 请求头: Authorization: Bearer <access_token>
# URL 参数: room_id - 自习室ID
# Query 参数:
#   ?date=2026-05-09   // 选填，日期 YYYY-MM-DD，默认当天
# 返回: { checkin_code: "A1B2C3", qr_code_url: null, code_date, ... }
# 注: 系统也会通过定时任务每日0点自动生成各自习室签到码
# ============================================================
@checkin_bp.route('/studyrooms/<int:room_id>/checkin-code', methods=['GET'])
@jwt_required()
def get_checkin_code(room_id):
    room = StudyRoom.query.get(room_id)
    if not room or room.is_del:
        return jsonify({'code': 404, 'message': '自习室不存在', 'data': None}), 404

    date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'code': 400, 'message': '日期格式错误', 'data': None}), 400

    code_record = RoomCheckInCode.query.filter_by(
        room_id=room_id,
        code_date=query_date
    ).first()

    if not code_record:
        code_record = RoomCheckInCode(
            room_id=room_id,
            code_date=query_date,
            checkin_code=_generate_code()
        )
        db.session.add(code_record)
        db.session.commit()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': code_record.to_dict()
    })


# ============================================================
# POST /api/v1/studyrooms/{room_id}/checkin-code/refresh
# 功能: 强制刷新今日签到码（管理员手动刷新）
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# URL 参数: room_id - 自习室ID
# 注: 会重新生成一个6位随机码替换现有签到码
# 返回: 新的签到码信息
# ============================================================
@checkin_bp.route('/studyrooms/<int:room_id>/checkin-code/refresh', methods=['POST'])
@jwt_required()
def refresh_checkin_code(room_id):
    room = StudyRoom.query.get(room_id)
    if not room or room.is_del:
        return jsonify({'code': 404, 'message': '自习室不存在', 'data': None}), 404

    today = date.today()
    code_record = RoomCheckInCode.query.filter_by(
        room_id=room_id,
        code_date=today
    ).first()

    new_code = _generate_code()

    if code_record:
        code_record.checkin_code = new_code
        code_record.created_at = datetime.now()
    else:
        code_record = RoomCheckInCode(
            room_id=room_id,
            code_date=today,
            checkin_code=new_code
        )
        db.session.add(code_record)

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '签到码已刷新',
        'data': code_record.to_dict()
    })