"""
角色权限管理模块单元测试
=========================
测试角色的列表查询、创建、更新、删除、权限查看与设置
"""
import pytest


class TestRoleList:
    """
    GET /api/v1/roles
    功能: 管理员获取所有角色列表
    权限: admin_required
    """

    def test_list_as_admin(self, client, admin_headers):
        """
        功能名: 角色列表
        功能简介: 管理员查询角色列表，验证系统预置3个角色
        类型: 正向测试
        URL: GET /api/v1/roles
        测试用例: 管理员 Token 请求角色列表
        预期结果: code=200, roles 数 >= 3, 含"学生""管理员""超级管理员"
        """
        resp = client.get('/api/v1/roles', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        roles = data['data']
        assert len(roles) >= 3
        names = [r['role_name'] for r in roles]
        assert '学生' in names
        assert '管理员' in names
        assert '超级管理员' in names


class TestRoleCreate:
    """
    POST /api/v1/roles
    功能: 超级管理员创建自定义角色
    权限: super_admin_required
    """

    def test_create_as_super_admin(self, client, admin_headers):
        """
        功能名: 创建角色
        功能简介: 超级管理员创建自定义角色
        类型: 正向测试
        URL: POST /api/v1/roles
        测试用例: role_name="测试角色", description="单元测试角色"
        预期结果: code=200, role_name="测试角色"
        """
        resp = client.post('/api/v1/roles', json={
            'role_name': '测试角色',
            'description': '单元测试角色'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['role_name'] == '测试角色'

    def test_create_duplicate_name(self, client, admin_headers):
        """
        功能名: 创建角色 - 名称重复
        功能简介: 创建已存在的角色名，验证唯一性校验
        类型: 反向测试（业务规则）
        URL: POST /api/v1/roles
        测试用例: 先创建"重复角色"，再用同名创建一次
        预期结果: 第二次 code=400, message 含"已存在"
        """
        client.post('/api/v1/roles', json={
            'role_name': '重复角色'
        }, headers=admin_headers)
        resp = client.post('/api/v1/roles', json={
            'role_name': '重复角色'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '已存在' in data['message']

    def test_create_empty_name(self, client, admin_headers):
        """
        功能名: 创建角色 - 空名称
        功能简介: 角色名为空字符串
        类型: 反向测试（参数校验）
        URL: POST /api/v1/roles
        测试用例: role_name=""
        预期结果: code=400
        """
        resp = client.post('/api/v1/roles', json={
            'role_name': ''
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 400


class TestRoleUpdate:
    """
    PUT /api/v1/roles/{role_id}
    功能: 超级管理员更新角色，系统预置角色不可修改
    权限: super_admin_required
    """

    def test_update_custom_role(self, client, admin_headers):
        """
        功能名: 更新角色
        功能简介: 超级管理员修改自定义角色的名称
        类型: 正向测试
        URL: PUT /api/v1/roles/{role_id}
        测试用例: 创建"可编辑角色"后修改为"已改名角色"
        预期结果: code=200, role_name="已改名角色"
        """
        create = client.post('/api/v1/roles', json={
            'role_name': '可编辑角色'
        }, headers=admin_headers)
        role_id = create.get_json()['data']['role_id']

        resp = client.put(f'/api/v1/roles/{role_id}', json={
            'role_name': '已改名角色'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['role_name'] == '已改名角色'

    def test_update_system_role_forbidden(self, client, admin_headers):
        """
        功能名: 更新角色 - 系统角色不可修改
        功能简介: 尝试修改系统预置角色（学生）
        类型: 反向测试（业务规则）
        URL: PUT /api/v1/roles/1
        测试用例: role_id=1（学生），role_name="新学生名"
        预期结果: code=400, message 含"不可修改"
        """
        resp = client.put('/api/v1/roles/1', json={
            'role_name': '新学生名'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '不可修改' in data['message']


class TestRoleDelete:
    """
    DELETE /api/v1/roles/{role_id}
    功能: 超级管理员删除角色（物理删除+清除关联权限），系统角色不可删除
    权限: super_admin_required
    """

    def test_delete_custom_role(self, client, admin_headers):
        """
        功能名: 删除角色
        功能简介: 超级管理员删除自定义角色
        类型: 正向测试
        URL: DELETE /api/v1/roles/{role_id}
        测试用例: 创建"待删除角色"后删除
        预期结果: code=200
        """
        create = client.post('/api/v1/roles', json={
            'role_name': '待删除角色'
        }, headers=admin_headers)
        role_id = create.get_json()['data']['role_id']

        resp = client.delete(f'/api/v1/roles/{role_id}',
                             headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200

    def test_delete_system_role_forbidden(self, client, admin_headers):
        """
        功能名: 删除角色 - 系统角色不可删除
        功能简介: 尝试删除系统预置角色（学生）
        类型: 反向测试（业务规则）
        URL: DELETE /api/v1/roles/1
        测试用例: role_id=1（学生）
        预期结果: code=400, message 含"不可删除"
        """
        resp = client.delete('/api/v1/roles/1', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '不可删除' in data['message']

    def test_delete_not_found(self, client, admin_headers):
        """
        功能名: 删除角色 - 不存在
        功能简介: 删除不存在的角色ID
        类型: 反向测试（资源不存在）
        URL: DELETE /api/v1/roles/99999
        测试用例: role_id=99999
        预期结果: code=404
        """
        resp = client.delete('/api/v1/roles/99999', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestRolePermissions:
    """
    GET /api/v1/roles/{role_id}/permissions  -- 查看角色权限
    PUT /api/v1/roles/{role_id}/permissions  -- 设置角色权限（覆盖式）
    权限: GET: admin_required, PUT: super_admin_required
    """

    def test_get_permissions(self, client, admin_headers):
        """
        功能名: 查看角色权限
        功能简介: 管理员查看学生角色的权限列表
        类型: 正向测试
        URL: GET /api/v1/roles/1/permissions
        测试用例: role_id=1（学生）
        预期结果: code=200, data 为列表
        """
        resp = client.get('/api/v1/roles/1/permissions',
                          headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert isinstance(data['data'], list)

    def test_set_permissions(self, client, admin_headers):
        """
        功能名: 设置角色权限
        功能简介: 超级管理员为自定义角色设置权限
        类型: 正向测试
        URL: PUT /api/v1/roles/{role_id}/permissions
        测试用例: 创建新角色后设置 perm_ids=[1,2,3]
        预期结果: code=200
        """
        create = client.post('/api/v1/roles', json={
            'role_name': '权限测试角色'
        }, headers=admin_headers)
        role_id = create.get_json()['data']['role_id']

        resp = client.put(f'/api/v1/roles/{role_id}/permissions', json={
            'perm_ids': [1, 2, 3]
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200

    def test_set_permissions_super_admin_forbidden(self, client, admin_headers):
        """
        功能名: 设置权限 - 禁止修改超级管理员权限
        功能简介: 尝试修改超级管理员角色的权限
        类型: 反向测试（业务规则）
        URL: PUT /api/v1/roles/3/permissions
        测试用例: role_id=3（超级管理员，第3个创建的），perm_ids=[1]
        预期结果: code=403, message 含"不允许"
        """
        super_role_id = 3
        resp = client.put(f'/api/v1/roles/{super_role_id}/permissions', json={
            'perm_ids': [1]
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 403
        assert '不允许' in data['message']

    def test_get_permissions_role_not_found(self, client, admin_headers):
        """
        功能名: 查看权限 - 角色不存在
        功能简介: 查看不存在角色的权限
        类型: 反向测试（资源不存在）
        URL: GET /api/v1/roles/99999/permissions
        测试用例: role_id=99999
        预期结果: code=404
        """
        resp = client.get('/api/v1/roles/99999/permissions',
                          headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404