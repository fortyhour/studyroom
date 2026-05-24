"""
违约记录模块单元测试
=========================
测试违约记录的分页查询（管理员全量、学生本人）、用户筛选、扩展信息
"""
import pytest


class TestViolationList:
    """
    GET /api/v1/violations
    功能: 分页查询违约记录，学生只能看自己的，管理员可看全部并可筛选用户
    权限: 需登录
    """

    def test_list_as_admin(self, client, admin_headers):
        """
        功能名: 违约列表 - 管理员查看全部
        功能简介: 管理员获取所有违约记录
        类型: 正向测试
        URL: GET /api/v1/violations
        测试用例: 管理员 Token（尚无违约记录）
        预期结果: code=200, items 为列表
        """
        resp = client.get('/api/v1/violations', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert isinstance(data['data']['items'], list)

    def test_list_as_student_empty(self, client, student_headers):
        """
        功能名: 违约列表 - 学生查看本人（空）
        功能简介: 学生查看自己的违约记录，新用户无记录
        类型: 正向测试（边界情况）
        URL: GET /api/v1/violations
        测试用例: 学生 Token（无违约记录）
        预期结果: code=200, total=0
        """
        resp = client.get('/api/v1/violations', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['total'] == 0

    def test_list_as_admin_with_user_filter(self, client, admin_headers):
        """
        功能名: 违约列表 - 管理员按用户筛选
        功能简介: 管理员筛选指定用户的违约记录
        类型: 正向测试
        URL: GET /api/v1/violations?user_id=1
        测试用例: ?user_id=1（admin用户）
        预期结果: code=200
        """
        resp = client.get('/api/v1/violations?user_id=1',
                          headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200

    def test_list_pagination(self, client, admin_headers):
        """
        功能名: 违约列表 - 分页
        功能简介: 验证分页参数生效
        类型: 正向测试
        URL: GET /api/v1/violations?page=1&size=5
        测试用例: ?page=1&size=5
        预期结果: code=200, size=5
        """
        resp = client.get('/api/v1/violations?page=1&size=5',
                          headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['size'] == 5