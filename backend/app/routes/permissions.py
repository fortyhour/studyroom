from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.permission import Permission

permissions_bp = Blueprint('permissions', __name__)


# ============================================================
# GET /api/v1/permissions
# 功能: 获取系统中所有可用权限列表（用于角色配置时选择权限）
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# 返回: 权限数组，每项含 perm_id、perm_name、perm_code、description
# ============================================================
@permissions_bp.route('', methods=['GET'])
@jwt_required()
def permission_list():
    perms = Permission.query.all()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [p.to_dict() for p in perms]
    })