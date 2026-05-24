"""
用户管理模块单元测试
=========================
测试管理员对用户的列表查询、详情、更新（邮箱/信誉分）、删除、角色分配
"""
import pytest


class TestUserList:
    """
    GET /api/v1/users
    功能: 管理员分页查询用户列表，支持关键词搜索
    权限: admin_required
    """

    def test_list_as_admin(self, client, admin_headers):
        """
        功能名: 用户列表 - 管理员查询
        功能简介: 管理员获取用户列表（至少含初始admin账号）
        类型: 正向测试
        URL: GET /api/v1/users
        测试用例: 管理员 Token 请求用户列表
        预期结果: code=200, items 为列表
        """
        resp = client.get('/api/v1/users', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert isinstance(data['data']['items'], list)

    def test_list_as_student_forbidden(self, client, student_headers):
        """
        功能名: 用户列表 - 学生越权
        功能简介: 学生角色尝试访问用户列表
        类型: 反向测试（权限不足）
        URL: GET /api/v1/users
        测试用例: 学生 Token 请求用户列表
        预期结果: code=403
        """
        resp = client.get('/api/v1/users', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 403

    def test_list_with_keyword(self, client, admin_headers):
        """
        功能名: 用户列表 - 关键词搜索
        功能简介: 按用户名关键词模糊搜索
        类型: 正向测试
        URL: GET /api/v1/users?keyword=searchable
        测试用例: 注册用户 "searchable_user"，用 ?keyword=searchable 搜索
        预期结果: code=200, total >= 1
        """
        client.post('/api/v1/auth/register', json={
            'username': 'searchable_user',
            'password': '123456'
        })
        resp = client.get('/api/v1/users?keyword=searchable',
                          headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['total'] >= 1

    def test_list_pagination(self, client, admin_headers):
        """
        功能名: 用户列表 - 分页
        功能简介: 验证分页参数生效
        类型: 正向测试
        URL: GET /api/v1/users?page=1&size=2
        测试用例: ?page=1&size=2
        预期结果: code=200, size=2
        """
        resp = client.get('/api/v1/users?page=1&size=2',
                          headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['size'] == 2


class TestUserDetail:
    """
    GET /api/v1/users/{user_id}
    功能: 管理员查看单个用户详情
    权限: admin_required
    """

    def test_get_detail_as_admin(self, client, admin_headers):
        """
        功能名: 用户详情
        功能简介: 管理员查看初始admin用户详情
        类型: 正向测试
        URL: GET /api/v1/users/1
        测试用例: user_id=1（初始admin）
        预期结果: code=200, username="admin"
        """
        resp = client.get('/api/v1/users/1', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['username'] == 'admin'

    def test_get_detail_not_found(self, client, admin_headers):
        """
        功能名: 用户详情 - 不存在
        功能简介: 查看不存在的用户ID
        类型: 反向测试（资源不存在）
        URL: GET /api/v1/users/99999
        测试用例: user_id=99999
        预期结果: code=404
        """
        resp = client.get('/api/v1/users/99999', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestUserUpdate:
    """
    PUT /api/v1/users/{user_id}
    功能: 管理员更新用户邮箱和信誉分
    权限: admin_required
    """

    def test_update_email(self, client, admin_headers):
        """
        功能名: 更新用户 - 邮箱
        功能简介: 管理员修改学生用户的邮箱
        类型: 正向测试
        URL: PUT /api/v1/users/2
        测试用例: 注册新用户(uid=2)，改为 email="new_email@qq.com"
        预期结果: code=200, email="new_email@qq.com"
        """
        client.post('/api/v1/auth/register', json={
            'username': 'update_me',
            'password': '123456'
        })
        resp = client.put('/api/v1/users/2', json={
            'email': 'new_email@qq.com'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['email'] == 'new_email@qq.com'

    def test_update_credit_score(self, client, admin_headers):
        """
        功能名: 更新用户 - 信誉分
        功能简介: 管理员调整用户的信誉分
        类型: 正向测试
        URL: PUT /api/v1/users/1
        测试用例: 将 admin 信誉分改为95
        预期结果: code=200, credit_score=95
        """
        resp = client.put('/api/v1/users/1', json={
            'credit_score': 95
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['credit_score'] == 95

    def test_update_not_found(self, client, admin_headers):
        """
        功能名: 更新用户 - 不存在
        功能简介: 更新不存在的用户
        类型: 反向测试（资源不存在）
        URL: PUT /api/v1/users/99999
        测试用例: user_id=99999, email="x@x.com"
        预期结果: code=404
        """
        resp = client.put('/api/v1/users/99999', json={
            'email': 'x@x.com'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestUserDelete:
    """
    DELETE /api/v1/users/{user_id}
    功能: 管理员软删除用户，不允许删除管理员角色用户
    权限: admin_required
    """

    def test_delete_student(self, client, admin_headers):
        """
        功能名: 删除用户 - 删除学生
        功能简介: 管理员软删除学生用户
        类型: 正向测试
        URL: DELETE /api/v1/users/2
        测试用例: 注册学生(uid=2)后删除，再查返回404
        预期结果: DELETE code=200, 再次 GET code=404
        """
        client.post('/api/v1/auth/register', json={
            'username': 'to_delete',
            'password': '123456'
        })
        resp = client.delete('/api/v1/users/2', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200

        resp2 = client.get('/api/v1/users/2', headers=admin_headers)
        assert resp2.get_json()['code'] == 404

    def test_delete_admin_forbidden(self, client, admin_headers):
        """
        功能名: 删除用户 - 禁止删除管理员
        功能简介: 尝试删除拥有管理员角色的用户
        类型: 反向测试（业务规则）
        URL: DELETE /api/v1/users/1
        测试用例: user_id=1（初始超级管理员admin）
        预期结果: code=403, message 含"不允许"
        """
        resp = client.delete('/api/v1/users/1', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 403
        assert '不允许' in data['message']

    def test_delete_not_found(self, client, admin_headers):
        """
        功能名: 删除用户 - 不存在
        功能简介: 删除不存在的用户
        类型: 反向测试（资源不存在）
        URL: DELETE /api/v1/users/99999
        测试用例: user_id=99999
        预期结果: code=404
        """
        resp = client.delete('/api/v1/users/99999', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestUserAssignRoles:
    """
    POST /api/v1/users/{user_id}/roles
    功能: 管理员为用户分配角色（覆盖式更新），不允许修改超级管理员角色
    权限: admin_required
    """

    def test_assign_roles_success(self, client, admin_headers):
        """
        功能名: 分配角色
        功能简介: 管理员为用户分配角色
        类型: 正向测试
        URL: POST /api/v1/users/2/roles
        测试用例: 注册新用户(uid=2)，分配角色 role_ids=[1,2]
        预期结果: code=200
        """
        client.post('/api/v1/auth/register', json={
            'username': 'role_test',
            'password': '123456'
        })
        resp = client.post('/api/v1/users/2/roles', json={
            'role_ids': [1, 2]
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200

    def test_assign_roles_super_admin_forbidden(self, client, admin_headers):
        """
        功能名: 分配角色 - 禁止修改超级管理员
        功能简介: 尝试修改超级管理员用户的角色
        类型: 反向测试（业务规则）
        URL: POST /api/v1/users/1/roles
        测试用例: 对 uid=1（超级管理员）尝试分配 role_ids=[1]
        预期结果: code=403, message 含"不允许"
        """
        resp = client.post('/api/v1/users/1/roles', json={
            'role_ids': [1]
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 403
        assert '不允许' in data['message']

    def test_assign_roles_user_not_found(self, client, admin_headers):
        """
        功能名: 分配角色 - 用户不存在
        功能简介: 对不存在的用户分配角色
        类型: 反向测试（资源不存在）
        URL: POST /api/v1/users/99999/roles
        测试用例: user_id=99999, role_ids=[1]
        预期结果: code=404
        """
        resp = client.post('/api/v1/users/99999/roles', json={
            'role_ids': [1]
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404