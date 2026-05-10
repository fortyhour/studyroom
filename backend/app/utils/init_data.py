from app.models.permission import Permission
from app import db

PERMISSIONS_DATA = [
    {'perm_name': '查看预约', 'perm_code': 'reservation:view', 'description': '查看预约记录'},
    {'perm_name': '创建预约', 'perm_code': 'reservation:create', 'description': '创建预约'},
    {'perm_name': '取消预约', 'perm_code': 'reservation:cancel', 'description': '取消预约'},
    {'perm_name': '签到', 'perm_code': 'reservation:checkin', 'description': '签到'},
    {'perm_name': '管理自习室', 'perm_code': 'room:manage', 'description': '增删改自习室'},
    {'perm_name': '管理座位', 'perm_code': 'seat:manage', 'description': '增删改座位'},
    {'perm_name': '管理用户', 'perm_code': 'user:manage', 'description': '管理用户和角色分配'},
    {'perm_name': '管理角色', 'perm_code': 'role:manage', 'description': '创建编辑角色和权限'},
    {'perm_name': '管理预约', 'perm_code': 'reservation:manage', 'description': '管理所有预约记录'},
    {'perm_name': '查看违约', 'perm_code': 'violation:view', 'description': '查看违约记录'},
    {'perm_name': '系统配置', 'perm_code': 'system:config', 'description': '修改系统参数'},
    {'perm_name': '查看统计', 'perm_code': 'statistics:view', 'description': '查看统计概览'},
]


def init_permissions():
    for perm_data in PERMISSIONS_DATA:
        if not Permission.query.filter_by(perm_code=perm_data['perm_code']).first():
            perm = Permission(**perm_data)
            db.session.add(perm)
    db.session.commit()


def init_roles():
    from app.models.role import Role, RolePermission

    student_role = Role.query.filter_by(role_name='学生').first()
    if not student_role:
        student_role = Role(role_name='学生', description='默认学生角色', is_system=True)
        db.session.add(student_role)
        db.session.flush()

    student_perms = ['reservation:view', 'reservation:create', 'reservation:cancel', 'reservation:checkin']
    for code in student_perms:
        perm = Permission.query.filter_by(perm_code=code).first()
        if perm:
            exists = RolePermission.query.filter_by(role_id=student_role.role_id, perm_id=perm.perm_id).first()
            if not exists:
                db.session.add(RolePermission(role_id=student_role.role_id, perm_id=perm.perm_id))

    admin_role = Role.query.filter_by(role_name='管理员').first()
    if not admin_role:
        admin_role = Role(role_name='管理员', description='默认管理员角色', is_system=True)
        db.session.add(admin_role)
        db.session.flush()

    admin_perms = ['room:manage', 'seat:manage', 'user:manage', 'reservation:manage',
                   'violation:view', 'statistics:view', 'reservation:view', 'reservation:cancel']
    for code in admin_perms:
        perm = Permission.query.filter_by(perm_code=code).first()
        if perm:
            exists = RolePermission.query.filter_by(role_id=admin_role.role_id, perm_id=perm.perm_id).first()
            if not exists:
                db.session.add(RolePermission(role_id=admin_role.role_id, perm_id=perm.perm_id))

    super_role = Role.query.filter_by(role_name='超级管理员').first()
    if not super_role:
        super_role = Role(role_name='超级管理员', description='超级管理员角色', is_system=True)
        db.session.add(super_role)
        db.session.flush()

    all_perms = Permission.query.all()
    for perm in all_perms:
        exists = RolePermission.query.filter_by(role_id=super_role.role_id, perm_id=perm.perm_id).first()
        if not exists:
            db.session.add(RolePermission(role_id=super_role.role_id, perm_id=perm.perm_id))

    db.session.commit()


def init_system_configs():
    from app.models.system_config import SystemConfig

    defaults = [
        {'config_key': 'MAX_RESERVATION_HOURS', 'config_value': '4', 'description': '最大预约小时数'},
        {'config_key': 'MAX_RESERVATION_DAYS', 'config_value': '7', 'description': '最大可预约天数'},
        {'config_key': 'CHECKIN_GRACE_MINUTES', 'config_value': '15', 'description': '签到宽限分钟数'},
        {'config_key': 'VIOLATION_PENALTY', 'config_value': '10', 'description': '违约扣分'},
        {'config_key': 'REMINDER_BEFORE_MINUTES', 'config_value': '15', 'description': '预约前提醒分钟数'},
        {'config_key': 'SECOND_REMINDER_MINUTES', 'config_value': '10', 'description': '第二次提醒（开始后分钟数）'},
    ]
    for cfg in defaults:
        if not SystemConfig.query.filter_by(config_key=cfg['config_key']).first():
            sc = SystemConfig(**cfg)
            db.session.add(sc)
    db.session.commit()


def init_admin_user():
    from app.models.user import User, UserRole
    from app.models.role import Role
    from werkzeug.security import generate_password_hash

    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            email='admin@univ.edu.cn',
            credit_score=100
        )
        db.session.add(admin)
        db.session.flush()

    super_role = Role.query.filter_by(role_name='超级管理员').first()
    if super_role:
        exists = UserRole.query.filter_by(user_id=admin.user_id, role_id=super_role.role_id).first()
        if not exists:
            db.session.add(UserRole(user_id=admin.user_id, role_id=super_role.role_id))

    db.session.commit()