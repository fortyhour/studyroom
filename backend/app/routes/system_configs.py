from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.system_config import SystemConfig
from app import db
from app.utils.decorators import admin_required

system_configs_bp = Blueprint('system_configs', __name__)


# ============================================================
# GET /api/v1/system-configs
# 功能: 获取所有系统配置项
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# 返回: 配置数组 [{config_key, config_value, description}, ...]
# 预置配置项: MAX_RESERVATION_HOURS / MAX_RESERVATION_DAYS / CHECKIN_GRACE_MINUTES /
#            VIOLATION_PENALTY / REMINDER_BEFORE_MINUTES / SECOND_REMINDER_MINUTES
# ============================================================
@system_configs_bp.route('', methods=['GET'])
@admin_required
def get_configs():
    configs = SystemConfig.query.all()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [c.to_dict() for c in configs]
    })


# ============================================================
# PUT /api/v1/system-configs/{config_key}
# 功能: 修改某个系统配置项的值
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: config_key - 配置键名，如 MAX_RESERVATION_HOURS
# 请求体 JSON:
#   { "config_value": 6 }     // 必填，新配置值（必须为数字）
# 限制: config_value 必须为正整数
# 返回: 更新后的配置信息
# ============================================================
@system_configs_bp.route('/<string:config_key>', methods=['PUT'])
@admin_required
def update_config(config_key):
    config = SystemConfig.query.filter_by(config_key=config_key).first()
    if not config:
        return jsonify({'code': 404, 'message': '配置项不存在', 'data': None}), 404

    data = request.get_json()
    if 'config_value' in data:
        raw_value = data['config_value']
        try:
            int_value = int(raw_value)
            if int_value <= 0:
                return jsonify({'code': 400, 'message': '配置值必须为正整数', 'data': None}), 400
        except (ValueError, TypeError):
            return jsonify({'code': 400, 'message': '配置值必须为数字', 'data': None}), 400
        config.config_value = str(int_value)

    db.session.commit()

    return jsonify({'code': 200, 'message': '更新成功', 'data': config.to_dict()})


# ============================================================
# GET /api/v1/system-configs/public
# 功能: 获取前端需要公开访问的配置项（无需管理员权限）
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# 返回: { "MAX_RESERVATION_DAYS": "7", "CHECKIN_GRACE_MINUTES": "15" }
# ============================================================
@system_configs_bp.route('/public', methods=['GET'])
@jwt_required()
def get_public_configs():
    keys = ['MAX_RESERVATION_DAYS', 'CHECKIN_GRACE_MINUTES']
    configs = SystemConfig.query.filter(SystemConfig.config_key.in_(keys)).all()
    result = {c.config_key: c.config_value for c in configs}
    return jsonify({'code': 200, 'message': 'success', 'data': result})