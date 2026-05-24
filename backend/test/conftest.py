import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from app.models.studyroom import StudyRoom
from app.models.seat import Seat
from app.models.system_config import SystemConfig
from app.models.checkin_code import RoomCheckInCode
from datetime import time


class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 86400
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = False


@pytest.fixture(scope='function')
def app():
    _app = create_app(config_class=TestConfig)
    with _app.app_context():
        db.create_all()
        yield _app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def _db(app):
    return db


@pytest.fixture(scope='function')
def student_token(client):
    client.post('/api/v1/auth/register', json={
        'username': 'test_student',
        'password': '123456',
        'email': 'test@univ.edu.cn'
    })
    resp = client.post('/api/v1/auth/login', json={
        'username': 'test_student',
        'password': '123456'
    })
    return resp.get_json()['data']['access_token']


@pytest.fixture(scope='function')
def student_headers(student_token):
    return {'Authorization': f'Bearer {student_token}'}


@pytest.fixture(scope='function')
def admin_token(client):
    resp = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    return resp.get_json()['data']['access_token']


@pytest.fixture(scope='function')
def admin_headers(admin_token):
    return {'Authorization': f'Bearer {admin_token}'}


@pytest.fixture(scope='function')
def test_room(client, admin_headers):
    resp = client.post('/api/v1/studyrooms', json={
        'room_name': '测试自习室',
        'location': '测试楼层',
        'open_time': '07:00',
        'close_time': '22:00',
        'description': '单元测试用自习室'
    }, headers=admin_headers)
    return resp.get_json()['data']


@pytest.fixture(scope='function')
def test_seat(client, admin_headers, test_room):
    resp = client.post(f'/api/v1/studyrooms/{test_room["room_id"]}/seats', json={
        'seat_number': 1,
        'has_power': True
    }, headers=admin_headers)
    return resp.get_json()['data']


@pytest.fixture(scope='function')
def test_seat2(client, admin_headers, test_room):
    resp = client.post(f'/api/v1/studyrooms/{test_room["room_id"]}/seats', json={
        'seat_number': 2,
        'has_power': False
    }, headers=admin_headers)
    return resp.get_json()['data']


@pytest.fixture(scope='function')
def test_seat3(client, admin_headers, test_room):
    resp = client.post(f'/api/v1/studyrooms/{test_room["room_id"]}/seats', json={
        'seat_number': 3,
        'has_power': True
    }, headers=admin_headers)
    return resp.get_json()['data']


@pytest.fixture(scope='function')
def test_checkin_code(client, admin_headers, test_room):
    resp = client.get(
        f'/api/v1/studyrooms/{test_room["room_id"]}/checkin-code',
        headers=admin_headers
    )
    return resp.get_json()['data']['checkin_code']