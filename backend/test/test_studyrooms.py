"""
自习室管理模块单元测试
=========================
测试自习室的列表查询、创建、详情、更新、删除接口
"""
import pytest


class TestStudyRoomList:
    """
    自习室列表查询测试
    GET /api/v1/studyrooms
    功能: 分页查询自习室列表，含实时空闲/占用/总数统计
    权限: 需登录（JWT Token）
    """

    def test_list_empty(self, client, student_headers):
        """
        功能名: 自习室列表 - 空列表
        功能简介: 查询自习室列表，数据库中尚无自习室
        类型: 正向测试（边界情况）
        URL: GET /api/v1/studyrooms
        测试用例: 学生登录后直接请求自习室列表（未创建任何自习室）
        预期结果: code=200, items 为空列表
        """
        resp = client.get('/api/v1/studyrooms', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert isinstance(data['data']['items'], list)

    def test_list_with_room(self, client, student_headers, test_room):
        """
        功能名: 自习室列表 - 含数据
        功能简介: 创建自习室后查询列表，验证统计字段
        类型: 正向测试
        URL: GET /api/v1/studyrooms
        测试用例: fixture 已创建 test_room（测试自习室），学生请求列表
        预期结果: code=200, items 数 >= 1, 每项含 total_seats/free_seats/occupied_seats
        """
        resp = client.get('/api/v1/studyrooms', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert len(data['data']['items']) >= 1
        room = data['data']['items'][0]
        assert 'total_seats' in room
        assert 'free_seats' in room
        assert 'occupied_seats' in room

    def test_list_with_location_filter(self, client, student_headers, test_room):
        """
        功能名: 自习室列表 - 位置筛选
        功能简介: 按位置关键词模糊搜索自习室
        类型: 正向测试
        URL: GET /api/v1/studyrooms?location=测试
        测试用例: 自习室位置含"测试"，用 ?location=测试 查询
        预期结果: code=200, items 数 >= 1
        """
        resp = client.get('/api/v1/studyrooms?location=测试', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert len(data['data']['items']) >= 1


class TestStudyRoomCreate:
    """
    自习室创建测试
    POST /api/v1/studyrooms
    功能: 创建新自习室
    权限: 管理员或超级管理员
    """

    def test_create_success(self, client, admin_headers):
        """
        功能名: 创建自习室
        功能简介: 管理员创建包含完整信息的自习室
        类型: 正向测试
        URL: POST /api/v1/studyrooms
        测试用例: room_name="新自习室", location="3楼", open_time="08:00", close_time="21:00"
        预期结果: code=200, room_name="新自习室", location="3楼", is_available=True
        """
        resp = client.post('/api/v1/studyrooms', json={
            'room_name': '新自习室',
            'location': '3楼',
            'open_time': '08:00',
            'close_time': '21:00',
            'description': '安静自习'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['room_name'] == '新自习室'
        assert data['data']['location'] == '3楼'
        assert data['data']['is_available'] is True

    def test_create_default_times(self, client, admin_headers):
        """
        功能名: 创建自习室 - 默认时间
        功能简介: 不传 open_time/close_time，验证默认值
        类型: 正向测试（默认值）
        URL: POST /api/v1/studyrooms
        测试用例: 只传 room_name="默认时间自习室"，不传时间参数
        预期结果: code=200, open_time="07:00:00", close_time="22:00:00"
        """
        resp = client.post('/api/v1/studyrooms', json={
            'room_name': '默认时间自习室'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['open_time'] == '07:00:00'
        assert data['data']['close_time'] == '22:00:00'

    def test_create_invalid_time_format(self, client, admin_headers):
        """
        功能名: 创建自习室 - 无效时间格式
        功能简介: 传入无法解析的时间字符串
        类型: 反向测试（参数格式错误）
        URL: POST /api/v1/studyrooms
        测试用例: open_time="bad"，无法被 strptime 解析
        预期结果: code=400
        """
        resp = client.post('/api/v1/studyrooms', json={
            'room_name': '坏时间',
            'open_time': 'bad'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 400

    def test_create_as_student_forbidden(self, client, student_headers):
        """
        功能名: 创建自习室 - 学生越权
        功能简介: 学生角色尝试创建自习室，验证权限控制
        类型: 反向测试（权限不足）
        URL: POST /api/v1/studyrooms
        测试用例: 学生 Token 请求创建自习室
        预期结果: code=403
        """
        resp = client.post('/api/v1/studyrooms', json={
            'room_name': '非法创建'
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 403


class TestStudyRoomDetail:
    """
    自习室详情测试
    GET /api/v1/studyrooms/{room_id}
    功能: 获取自习室详情，含座位列表和占用状态
    权限: 需登录
    """

    def test_get_detail(self, client, student_headers, test_room):
        """
        功能名: 自习室详情
        功能简介: 查询存在的自习室详情，验证返回 seats 数组
        类型: 正向测试
        URL: GET /api/v1/studyrooms/{room_id}
        测试用例: 用 fixture 创建的 test_room 的 ID 请求详情
        预期结果: code=200, room_name="测试自习室", 含 seats 字段
        """
        resp = client.get(f'/api/v1/studyrooms/{test_room["room_id"]}',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['room_name'] == '测试自习室'
        assert 'seats' in data['data']

    def test_get_detail_not_found(self, client, student_headers):
        """
        功能名: 自习室详情 - 不存在
        功能简介: 查询不存在的自习室 ID
        类型: 反向测试（资源不存在）
        URL: GET /api/v1/studyrooms/99999
        测试用例: room_id=99999
        预期结果: code=404
        """
        resp = client.get('/api/v1/studyrooms/99999', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestStudyRoomUpdate:
    """
    自习室更新测试
    PUT /api/v1/studyrooms/{room_id}
    功能: 更新自习室信息（名称、位置、时间、是否开放等）
    权限: 管理员或超级管理员
    """

    def test_update_success(self, client, admin_headers, test_room):
        """
        功能名: 更新自习室
        功能简介: 管理员修改自习室名称和关闭自习室
        类型: 正向测试
        URL: PUT /api/v1/studyrooms/{room_id}
        测试用例: room_name="改名自习室", is_available=False
        预期结果: code=200, room_name="改名自习室", is_available=False
        """
        resp = client.put(f'/api/v1/studyrooms/{test_room["room_id"]}', json={
            'room_name': '改名自习室',
            'is_available': False
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['room_name'] == '改名自习室'
        assert data['data']['is_available'] is False

    def test_update_not_found(self, client, admin_headers):
        """
        功能名: 更新自习室 - 不存在
        功能简介: 更新不存在的自习室 ID
        类型: 反向测试（资源不存在）
        URL: PUT /api/v1/studyrooms/99999
        测试用例: room_id=99999, room_name="不存在"
        预期结果: code=404
        """
        resp = client.put('/api/v1/studyrooms/99999', json={
            'room_name': '不存在'
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestStudyRoomDelete:
    """
    自习室删除测试
    DELETE /api/v1/studyrooms/{room_id}
    功能: 软删除自习室（is_del=1）
    权限: 管理员或超级管理员
    """

    def test_delete_success(self, client, admin_headers, test_room):
        """
        功能名: 删除自习室
        功能简介: 软删除自习室后，再次查询返回 404
        类型: 正向测试
        URL: DELETE /api/v1/studyrooms/{room_id}
        测试用例: 删除 fixture 创建的 test_room，再 GET 查询
        预期结果: DELETE code=200, 再次 GET code=404
        """
        resp = client.delete(f'/api/v1/studyrooms/{test_room["room_id"]}',
                             headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200

        resp2 = client.get(f'/api/v1/studyrooms/{test_room["room_id"]}',
                           headers=admin_headers)
        assert resp2.get_json()['code'] == 404

    def test_delete_not_found(self, client, admin_headers):
        """
        功能名: 删除自习室 - 不存在
        功能简介: 删除不存在的自习室 ID
        类型: 反向测试（资源不存在）
        URL: DELETE /api/v1/studyrooms/99999
        测试用例: room_id=99999
        预期结果: code=404
        """
        resp = client.delete('/api/v1/studyrooms/99999', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404