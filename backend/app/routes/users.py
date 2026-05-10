from flask import Blueprint, request, jsonify
from app.models.user import User, UserRole
from app.models.role import Role
from app import db
from app.utils.decorators import admin_required

users_bp = Blueprint('users', __name__)


# ============================================================
# GET /api/v1/users
# 功能: 获取用户列表（分页、搜索）
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# Query 参数:
#   ?page=1       // 页码，默认1
#   &size=10      // 每页条数，默认10
#   &keyword=     // 按学号/工号模糊搜索，可选
# 返回: 分页用户列表，含角色信息
# ============================================================
@users_bp.route('/users', methods=['GET'])
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    keyword = request.args.get('keyword', '')

    query = User.query.filter(User.is_del == 0)
    if keyword:
        query = query.filter(User.username.contains(keyword))

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=size, error_out=False)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': [u.to_dict() for u in pagination.items],
            'total': pagination.total,
            'page': page,
            'size': size,
            'pages': pagination.pages
        }
    })


# ============================================================
# GET /api/v1/users/{user_id}
# 功能: 获取单个用户详情
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: user_id - 用户ID
# 返回: 用户基本信息、角色列表
# ============================================================
@users_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def user_detail(user_id):
    user = User.query.get(user_id)
    if not user or user.is_del:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404

    return jsonify({'code': 200, 'message': 'success', 'data': user.to_dict()})


# ============================================================
# PUT /api/v1/users/{user_id}
# 功能: 更新用户信息
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: user_id - 用户ID
# 请求体 JSON:
#   {
#     "email": "new@qq.com",      // 选填，邮箱
#     "credit_score": 90          // 选填，信誉分
#   }
# 返回: 更新后的用户信息
# ============================================================
@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user or user.is_del:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404

    data = request.get_json()
    if 'email' in data:
        user.email = data['email']
    if 'credit_score' in data:
        user.credit_score = data['credit_score']

    db.session.commit()

    return jsonify({'code': 200, 'message': '更新成功', 'data': user.to_dict()})


# ============================================================
# DELETE /api/v1/users/{user_id}
# 功能: 删除用户（软删除）
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: user_id - 用户ID
# 限制: 不允许删除拥有"管理员"或"超级管理员"角色的用户
# 返回: 操作结果
# ============================================================
@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user or user.is_del:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404

    is_admin_user = any(role.role_name in ['管理员', '超级管理员'] for role in user.roles)
    if is_admin_user:
        return jsonify({'code': 403, 'message': '不允许删除管理员账号', 'data': None}), 403

    user.is_del = 1
    db.session.commit()

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


# ============================================================
# POST /api/v1/users/{user_id}/roles
# 功能: 为用户分配角色（覆盖式更新）
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: user_id - 用户ID
# 请求体 JSON:
#   { "role_ids": [1, 2] }   // 角色ID数组，会覆盖该用户所有现有角色
# 限制: 不允许修改超级管理员的角色
# 返回: 更新后的用户信息（含新角色）
# ============================================================
@users_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@admin_required
def assign_roles(user_id):
    user = User.query.get(user_id)
    if not user or user.is_del:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404

    is_super_admin = any(role.role_name == '超级管理员' for role in user.roles)
    if is_super_admin:
        return jsonify({'code': 403, 'message': '不允许修改超级管理员的角色', 'data': None}), 403

    data = request.get_json()
    role_ids = data.get('role_ids', [])

    UserRole.query.filter_by(user_id=user_id).delete()

    for role_id in role_ids:
        role = Role.query.get(role_id)
        if role:
            db.session.add(UserRole(user_id=user_id, role_id=role_id))

    db.session.commit()

    return jsonify({'code': 200, 'message': '角色分配成功', 'data': user.to_dict()})