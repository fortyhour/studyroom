from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify
from app.models.user import User
from app.models.role import RolePermission, Role


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 401, 'message': '用户不存在', 'data': None}), 401
        is_admin = any(role.role_name in ['管理员', '超级管理员'] for role in user.roles)
        if not is_admin:
            return jsonify({'code': 403, 'message': '需要管理员权限', 'data': None}), 403
        return fn(*args, **kwargs)
    return wrapper


def super_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 401, 'message': '用户不存在', 'data': None}), 401
        is_super = any(role.role_name == '超级管理员' for role in user.roles)
        if not is_super:
            return jsonify({'code': 403, 'message': '需要超级管理员权限', 'data': None}), 403
        return fn(*args, **kwargs)
    return wrapper


def permission_required(perm_code):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                return jsonify({'code': 401, 'message': '用户不存在', 'data': None}), 401
            for role in user.roles:
                for perm in role.permissions:
                    if perm.perm_code == perm_code:
                        return fn(*args, **kwargs)
            return jsonify({'code': 403, 'message': f'缺少权限: {perm_code}', 'data': None}), 403
        return wrapper
    return decorator