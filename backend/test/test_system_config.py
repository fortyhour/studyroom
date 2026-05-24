"""
系统配置模块单元测试
=========================
测试系统配置的查询（管理员）、更新（含格式校验）、公开配置获取
"""
import pytest


class TestSystemConfigGet:
    """
    GET /api/v1/system-configs
    功能: 管理员获取所有系统配置项
    权限: admin_required
    """

    def test_get_as_admin(self, client, admin_headers):
        """
        功能名: 系统配置 - 管理员获取全部配置
        功能简介: 管理员获取系统配置列表，验证预置6项配置存在
        类型: 正向测试
        URL: GET /api/v1/system-configs
        测试用例: 管理员 Token 请求全部配置
        预期结果: code=200, 含 MAX_RESERVATION_HOURS、MAX_RESERVATION_DAYS、CHECKIN_GRACE_MINUTES
        """
        resp = client.get('/api/v1/system-configs', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert isinstance(data['data'], list)
        configs = {c['config_key']: c['config_value'] for c in data['data']}
        assert 'MAX_RESERVATION_HOURS' in configs
        assert 'MAX_RESERVATION_DAYS' in configs
        assert 'CHECKIN_GRACE_MINUTES' in configs

    def test_get_as_student_forbidden(self, client, student_headers):
        """
        功能名: 系统配置 - 学生越权
        功能简介: 学生角色尝试获取全部系统配置
        类型: 反向测试（权限不足）
        URL: GET /api/v1/system-configs
        测试用例: 学生 Token 请求系统配置
        预期结果: code=403
        """
        resp = client.get('/api/v1/system-configs', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 403


class TestSystemConfigUpdate:
    """
    PUT /api/v1/system-configs/{config_key}
    功能: 管理员修改系统配置项的值，config_value 必须为正整数
    权限: admin_required
    """

    def test_update_success(self, client, admin_headers):
        """
        功能名: 更新配置 - 修改最大预约时长
        功能简介: 管理员将 MAX_RESERVATION_HOURS 从4改为6
        类型: 正向测试
        URL: PUT /api/v1/system-configs/MAX_RESERVATION_HOURS
        测试用例: config_value=6
        预期结果: code=200, config_value="6"
        """
        resp = client.put('/api/v1/system-configs/MAX_RESERVATION_HOURS', json={
            'config_value': 6
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['config_value'] == '6'

    def test_update_non_integer(self, client, admin_headers):
        """
        功能名: 更新配置 - 非数字值
        功能简介: config_value 传入字母字符串
        类型: 反向测试（格式校验）
        URL: PUT /api/v1/system-configs/MAX_RESERVATION_HOURS
        测试用例: config_value="abc"
        预期结果: code=400, message 含"数字"
        """
        resp = client.put('/api/v1/system-configs/MAX_RESERVATION_HOURS', json={
            'config_value': 'abc'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '数字' in data['message']

    def test_update_non_positive(self, client, admin_headers):
        """
        功能名: 更新配置 - 零值
        功能简介: config_value 传入0（非正整数）
        类型: 反向测试（业务规则）
        URL: PUT /api/v1/system-configs/MAX_RESERVATION_HOURS
        测试用例: config_value=0
        预期结果: code=400, message 含"正整数"
        """
        resp = client.put('/api/v1/system-configs/MAX_RESERVATION_HOURS', json={
            'config_value': 0
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '正整数' in data['message']

    def test_update_negative(self, client, admin_headers):
        """
        功能名: 更新配置 - 负数
        功能简介: config_value 传入负数
        类型: 反向测试（业务规则）
        URL: PUT /api/v1/system-configs/MAX_RESERVATION_HOURS
        测试用例: config_value=-1
        预期结果: code=400
        """
        resp = client.put('/api/v1/system-configs/MAX_RESERVATION_HOURS', json={
            'config_value': -1
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 400

    def test_update_not_found(self, client, admin_headers):
        """
        功能名: 更新配置 - 配置键不存在
        功能简介: 修改不存在的配置项
        类型: 反向测试（资源不存在）
        URL: PUT /api/v1/system-configs/NONEXISTENT_KEY
        测试用例: config_key="NONEXISTENT_KEY", config_value=1
        预期结果: code=404
        """
        resp = client.put('/api/v1/system-configs/NONEXISTENT_KEY', json={
            'config_value': 1
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestPublicConfigs:
    """
    GET /api/v1/system-configs/public
    功能: 获取前端需要的公开配置项（无需管理员权限）
    权限: 需登录（普通用户也可）
    """

    def test_get_public_as_student(self, client, student_headers):
        """
        功能名: 公开配置 - 学生获取
        功能简介: 学生获取前端所需公开配置（MAX_RESERVATION_DAYS、CHECKIN_GRACE_MINUTES）
        类型: 正向测试
        URL: GET /api/v1/system-configs/public
        测试用例: 学生 Token 请求公开配置
        预期结果: code=200, 含 MAX_RESERVATION_DAYS 和 CHECKIN_GRACE_MINUTES
        """
        resp = client.get('/api/v1/system-configs/public',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert 'MAX_RESERVATION_DAYS' in data['data']
        assert 'CHECKIN_GRACE_MINUTES' in data['data']