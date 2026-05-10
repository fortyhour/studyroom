from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_apscheduler import APScheduler
from app.config import Config

db = SQLAlchemy()
jwt = JWTManager()
scheduler = APScheduler()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    scheduler.init_app(app)
    scheduler.start()

    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.roles import roles_bp
    from app.routes.permissions import permissions_bp
    from app.routes.studyrooms import studyrooms_bp
    from app.routes.seats import seats_bp
    from app.routes.reservations import reservations_bp
    from app.routes.checkin import checkin_bp
    from app.routes.violations import violations_bp
    from app.routes.system_configs import system_configs_bp
    from app.routes.statistics import statistics_bp
    from app.routes.ai import ai_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1')
    app.register_blueprint(roles_bp, url_prefix='/api/v1/roles')
    app.register_blueprint(permissions_bp, url_prefix='/api/v1/permissions')
    app.register_blueprint(studyrooms_bp, url_prefix='/api/v1/studyrooms')
    app.register_blueprint(seats_bp, url_prefix='/api/v1')
    app.register_blueprint(reservations_bp, url_prefix='/api/v1/reservations')
    app.register_blueprint(checkin_bp, url_prefix='/api/v1')
    app.register_blueprint(violations_bp, url_prefix='/api/v1/violations')
    app.register_blueprint(system_configs_bp, url_prefix='/api/v1/system-configs')
    app.register_blueprint(statistics_bp, url_prefix='/api/v1/statistics')
    app.register_blueprint(ai_bp, url_prefix='/api/v1/ai')

    with app.app_context():
        from app.models import user, role, permission, studyroom, seat, reservation, violation, system_config, checkin_code
        db.create_all()
        from app.utils.init_data import init_permissions, init_roles, init_system_configs, init_admin_user
        init_permissions()
        init_roles()
        init_system_configs()
        init_admin_user()
        from app.utils.scheduled_tasks import register_tasks
        register_tasks(scheduler, app)

    return app