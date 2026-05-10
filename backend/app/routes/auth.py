from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app import db

auth_bp = Blueprint('auth', __name__)


# ============================================================
# POST /api/v1/auth/register
# 功能: 用户注册
# 权限: 无需登录
# 请求体 JSON:
#   {
#     "username": "2024001",   // 必填，学号/工号
#     "password": "123456",    // 必填，密码
#     "email": "xx@univ.edu.cn" // 选填，邮箱
#   }
# 返回: 用户信息（不含密码），自动分配"学生"角色，初始信誉分100
# ============================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空', 'data': None}), 400

    if User.query.filter_by(username=username, is_del=0).first():
        return jsonify({'code': 400, 'message': '用户名已存在', 'data': None}), 400

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        email=email,
        credit_score=100
    )
    db.session.add(user)
    db.session.flush()

    from app.models.role import Role
    from app.models.user import UserRole
    student_role = Role.query.filter_by(role_name='学生').first()
    if student_role:
        db.session.add(UserRole(user_id=user.user_id, role_id=student_role.role_id))

    db.session.commit()

    return jsonify({'code': 200, 'message': '注册成功', 'data': user.to_dict()})


# ============================================================
# POST /api/v1/auth/login
# 功能: 用户登录，获取 JWT Token
# 权限: 无需登录
# 请求体 JSON:
#   {
#     "username": "2024001",   // 必填，学号/工号
#     "password": "123456"     // 必填，密码
#   }
# 返回:
#   {
#     "access_token": "xxx",   // JWT Token
#     "token_type": "bearer",
#     "user": { "user_id":1, "username":"...", "roles":[...], ... }
#   }
# ============================================================
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空', 'data': None}), 400

    user = User.query.filter_by(username=username, is_del=0).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'code': 401, 'message': '用户名或密码错误', 'data': None}), 401

    access_token = create_access_token(identity=str(user.user_id))

    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'access_token': access_token,
            'token_type': 'bearer',
            'user': user.to_dict()
        }
    })


# ============================================================
# GET /api/v1/auth/me
# 功能: 获取当前登录用户信息及角色权限列表
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# 返回: 用户基本信息 + roles数组 + permissions数组
# ============================================================
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.is_del:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404

    user_data = user.to_dict()
    user_data['roles'] = [{'role_id': r.role_id, 'role_name': r.role_name} for r in user.roles]
    perms = set()
    for role in user.roles:
        for perm in role.permissions:
            perms.add(perm.perm_code)
    user_data['permissions'] = list(perms)

    return jsonify({'code': 200, 'message': 'success', 'data': user_data})


# ============================================================
# PUT /api/v1/auth/me
# 功能: 当前用户修改自己的个人信息（邮箱）
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# 请求体 JSON:
#   { "email": "new@qq.com" }   // 选填，邮箱
# 返回: 更新后的用户信息
# ============================================================
@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.is_del:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404

    data = request.get_json()
    if 'email' in data:
        user.email = data['email']

    db.session.commit()

    return jsonify({'code': 200, 'message': '更新成功', 'data': user.to_dict()})


# ============================================================
# POST /api/v1/auth/logout
# 功能: 登出（客户端丢弃令牌即可，服务端无状态）
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# ============================================================
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'code': 200, 'message': '登出成功', 'data': None})