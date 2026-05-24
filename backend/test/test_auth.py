"""
用户认证模块单元测试
=========================
测试注册、登录、获取个人信息、修改个人信息、登出等接口
"""
import pytest


class TestRegister:
    """
    注册接口测试
    POST /api/v1/auth/register
    功能: 新用户注册，自动分配"学生"角色，初始信誉分100
    """

    def test_register_success(self, client):
        """
        功能名: 用户注册
        功能简介: 使用合法的用户名、密码、邮箱注册新用户
        类型: 正向测试
        URL: POST /api/v1/auth/register
        测试用例: username="new_user", password="123456", email="new@univ.edu.cn"
        预期结果: code=200, username=new_user, credit_score=100, roles含"学生"
        """
        resp = client.post('/api/v1/auth/register', json={
            'username': 'new_user',
            'password': '123456',
            'email': 'new@univ.edu.cn'
        })
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['username'] == 'new_user'
        assert data['data']['credit_score'] == 100
        assert '学生' in data['data']['roles']

    def test_register_missing_username(self, client):
        """
        功能名: 用户注册 - 缺少用户名
        功能简介: 请求体中不传 username 字段，验证参数校验
        类型: 反向测试（参数缺失）
        URL: POST /api/v1/auth/register
        测试用例: 只传 password="123456"，不传 username
        预期结果: code=400, message 含"用户名"
        """
        resp = client.post('/api/v1/auth/register', json={
            'password': '123456'
        })
        data = resp.get_json()
        assert data['code'] == 400
        assert '用户名' in data['message']

    def test_register_missing_password(self, client):
        """
        功能名: 用户注册 - 缺少密码
        功能简介: 请求体中不传 password 字段，验证参数校验
        类型: 反向测试（参数缺失）
        URL: POST /api/v1/auth/register
        测试用例: 只传 username="test_user"，不传 password
        预期结果: code=400, message 含"密码"
        """
        resp = client.post('/api/v1/auth/register', json={
            'username': 'test_user'
        })
        data = resp.get_json()
        assert data['code'] == 400
        assert '密码' in data['message']

    def test_register_duplicate_username(self, client):
        """
        功能名: 用户注册 - 重复用户名
        功能简介: 使用已存在的用户名再次注册，验证唯一性校验
        类型: 反向测试（业务规则）
        URL: POST /api/v1/auth/register
        测试用例: 先用 "dup_user" 注册一次，再用同一用户名注册第二次
        预期结果: 第二次注册 code=400, message 含"已存在"
        """
        client.post('/api/v1/auth/register', json={
            'username': 'dup_user',
            'password': '123456'
        })
        resp = client.post('/api/v1/auth/register', json={
            'username': 'dup_user',
            'password': '654321'
        })
        data = resp.get_json()
        assert data['code'] == 400
        assert '已存在' in data['message']


class TestLogin:
    """
    登录接口测试
    POST /api/v1/auth/login
    功能: 验证用户名密码，成功返回 JWT access_token 和用户信息
    """

    def test_login_success(self, client, student_token):
        """
        功能名: 用户登录
        功能简介: 使用正确的用户名密码登录，获取 JWT Token
        类型: 正向测试
        URL: POST /api/v1/auth/login
        测试用例: fixture 已注册 test_student/123456，通过 student_token 验证
        预期结果: student_token 非空且长度 > 0
        """
        assert student_token is not None
        assert len(student_token) > 0

    def test_login_wrong_password(self, client):
        """
        功能名: 用户登录 - 密码错误
        功能简介: 使用正确的用户名 + 错误的密码尝试登录
        类型: 反向测试（认证失败）
        URL: POST /api/v1/auth/login
        测试用例: 先注册 test_login/123456，再用密码 "wrong" 登录
        预期结果: code=401
        """
        client.post('/api/v1/auth/register', json={
            'username': 'test_login',
            'password': '123456'
        })
        resp = client.post('/api/v1/auth/login', json={
            'username': 'test_login',
            'password': 'wrong'
        })
        data = resp.get_json()
        assert data['code'] == 401

    def test_login_nonexistent_user(self, client):
        """
        功能名: 用户登录 - 用户不存在
        功能简介: 使用不存在的用户名尝试登录
        类型: 反向测试（用户不存在）
        URL: POST /api/v1/auth/login
        测试用例: username="no_such_user", password="123456"
        预期结果: code=401
        """
        resp = client.post('/api/v1/auth/login', json={
            'username': 'no_such_user',
            'password': '123456'
        })
        data = resp.get_json()
        assert data['code'] == 401

    def test_login_missing_fields(self, client):
        """
        功能名: 用户登录 - 缺少参数
        功能简介: 只传 username 不传 password，验证参数完整性校验
        类型: 反向测试（参数缺失）
        URL: POST /api/v1/auth/login
        测试用例: 只传 username="test"，不传 password
        预期结果: code=400
        """
        resp = client.post('/api/v1/auth/login', json={
            'username': 'test'
        })
        data = resp.get_json()
        assert data['code'] == 400


class TestMe:
    """
    个人中心接口测试
    GET/PUT /api/v1/auth/me
    功能: 获取/修改当前登录用户信息
    """

    def test_get_me_success(self, client, student_headers):
        """
        功能名: 获取当前用户信息
        功能简介: 使用有效 JWT Token 获取个人资料和权限
        类型: 正向测试
        URL: GET /api/v1/auth/me
        测试用例: 携带 student_headers（test_student 的 Token）请求
        预期结果: code=200, username="test_student", 含 roles 和 permissions
        """
        resp = client.get('/api/v1/auth/me', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['username'] == 'test_student'
        assert 'roles' in data['data']
        assert 'permissions' in data['data']

    def test_get_me_without_token(self, client):
        """
        功能名: 获取当前用户信息 - 未登录
        功能简介: 不带 JWT Token 请求个人中心，验证鉴权
        类型: 反向测试（未授权）
        URL: GET /api/v1/auth/me
        测试用例: 不携带 Authorization 请求头
        预期结果: code=401
        """
        resp = client.get('/api/v1/auth/me')
        data = resp.get_json()
        assert data['code'] == 401

    def test_update_me_email(self, client, student_headers):
        """
        功能名: 修改个人信息 - 邮箱
        功能简介: 当前登录用户修改自己的邮箱地址
        类型: 正向测试
        URL: PUT /api/v1/auth/me
        测试用例: email="updated@univ.edu.cn"
        预期结果: code=200, email="updated@univ.edu.cn"
        """
        resp = client.put('/api/v1/auth/me', json={
            'email': 'updated@univ.edu.cn'
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['email'] == 'updated@univ.edu.cn'


class TestLogout:
    """
    登出接口测试
    POST /api/v1/auth/logout
    功能: 用户登出（JWT 无状态，仅返回成功消息）
    """

    def test_logout_success(self, client, student_headers):
        """
        功能名: 用户登出
        功能简介: 已登录用户调用登出接口
        类型: 正向测试
        URL: POST /api/v1/auth/logout
        测试用例: 携带有效 JWT Token 请求登出
        预期结果: code=200
        """
        resp = client.post('/api/v1/auth/logout', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200

    def test_logout_without_token(self, client):
        """
        功能名: 用户登出 - 未登录
        功能简介: 不带 JWT Token 调用登出接口，验证鉴权
        类型: 反向测试（未授权）
        URL: POST /api/v1/auth/logout
        测试用例: 不携带 Authorization 请求头
        预期结果: code=401
        """
        resp = client.post('/api/v1/auth/logout')
        data = resp.get_json()
        assert data['code'] == 401