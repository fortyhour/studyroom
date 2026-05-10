from flask import Blueprint, request, jsonify
from app.models.role import Role, RolePermission
from app.models.permission import Permission
from app import db
from app.utils.decorators import super_admin_required, admin_required

roles_bp = Blueprint('roles', __name__)


# ============================================================
# GET /api/v1/roles
# 功能: 获取所有角色列表
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# 返回: 角色数组（不含权限详情，仅基本信息）
# ============================================================
@roles_bp.route('', methods=['GET'])
@admin_required
def role_list():
    roles = Role.query.all()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [r.to_simple_dict() for r in roles]
    })


# ============================================================
# POST /api/v1/roles
# 功能: 创建新角色
# 权限: 仅超级管理员
# 请求头: Authorization: Bearer <super_admin_token>
# 请求体 JSON:
#   {
#     "role_name": "运营",     // 必填，角色名称，不可重复
#     "description": "运维人员"  // 选填，角色描述
#   }
# 返回: 创建的角色信息
# ============================================================
@roles_bp.route('', methods=['POST'])
@super_admin_required
def create_role():
    data = request.get_json()
    role_name = data.get('role_name')
    description = data.get('description', '')

    if not role_name:
        return jsonify({'code': 400, 'message': '角色名不能为空', 'data': None}), 400

    if Role.query.filter_by(role_name=role_name).first():
        return jsonify({'code': 400, 'message': '角色名已存在', 'data': None}), 400

    role = Role(role_name=role_name, description=description)
    db.session.add(role)
    db.session.commit()

    return jsonify({'code': 200, 'message': '创建成功', 'data': role.to_dict()})


# ============================================================
# PUT /api/v1/roles/{role_id}
# 功能: 更新角色信息
# 权限: 仅超级管理员
# 请求头: Authorization: Bearer <super_admin_token>
# URL 参数: role_id - 角色ID
# 请求体 JSON:
#   {
#     "role_name": "新名称",     // 选填
#     "description": "新描述"    // 选填
#   }
# 限制: 系统预置角色（is_system=true）不可修改
# 返回: 更新后的角色信息
# ============================================================
@roles_bp.route('/<int:role_id>', methods=['PUT'])
@super_admin_required
def update_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'code': 404, 'message': '角色不存在', 'data': None}), 404

    if role.is_system:
        return jsonify({'code': 400, 'message': '系统预置角色不可修改', 'data': None}), 400

    data = request.get_json()
    if 'role_name' in data:
        role.role_name = data['role_name']
    if 'description' in data:
        role.description = data['description']

    db.session.commit()

    return jsonify({'code': 200, 'message': '更新成功', 'data': role.to_dict()})


# ============================================================
# DELETE /api/v1/roles/{role_id}
# 功能: 删除角色（物理删除，同时清除关联权限）
# 权限: 仅超级管理员
# 请求头: Authorization: Bearer <super_admin_token>
# URL 参数: role_id - 角色ID
# 限制: 系统预置角色（is_system=true）不可删除
# 返回: 操作结果
# ============================================================
@roles_bp.route('/<int:role_id>', methods=['DELETE'])
@super_admin_required
def delete_role(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'code': 404, 'message': '角色不存在', 'data': None}), 404

    if role.is_system:
        return jsonify({'code': 400, 'message': '系统预置角色不可删除', 'data': None}), 400

    RolePermission.query.filter_by(role_id=role_id).delete()
    db.session.delete(role)
    db.session.commit()

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


# ============================================================
# GET /api/v1/roles/{role_id}/permissions
# 功能: 查看某个角色的权限列表
# 权限: 管理员或超级管理员
# 请求头: Authorization: Bearer <admin_token>
# URL 参数: role_id - 角色ID
# 返回: 该角色拥有的权限列表
# ============================================================
@roles_bp.route('/<int:role_id>/permissions', methods=['GET'])
@admin_required
def role_permissions(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'code': 404, 'message': '角色不存在', 'data': None}), 404

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [p.to_dict() for p in role.permissions]
    })


# ============================================================
# PUT /api/v1/roles/{role_id}/permissions
# 功能: 设置角色的权限（覆盖式更新）
# 权限: 仅超级管理员
# 请求头: Authorization: Bearer <super_admin_token>
# URL 参数: role_id - 角色ID
# 请求体 JSON:
#   { "perm_ids": [1, 3, 5] }   // 权限ID数组，会覆盖该角色所有现有权限
# 限制: 不允许修改"超级管理员"角色的权限
# 返回: 更新后角色的权限列表
# ============================================================
@roles_bp.route('/<int:role_id>/permissions', methods=['PUT'])
@super_admin_required
def set_role_permissions(role_id):
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'code': 404, 'message': '角色不存在', 'data': None}), 404

    if role.role_name == '超级管理员':
        return jsonify({'code': 403, 'message': '不允许修改超级管理员的权限', 'data': None}), 403

    data = request.get_json()
    perm_ids = data.get('perm_ids', [])

    RolePermission.query.filter_by(role_id=role_id).delete()

    for perm_id in perm_ids:
        perm = Permission.query.get(perm_id)
        if perm:
            db.session.add(RolePermission(role_id=role_id, perm_id=perm_id))

    db.session.commit()

    return jsonify({'code': 200, 'message': '权限设置成功', 'data': [p.to_dict() for p in role.permissions]})