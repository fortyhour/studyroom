"""
座位管理模块单元测试
=========================
测试座位的列表查询、创建、详情、更新、删除、可用时段查询接口
"""
import pytest


class TestSeatList:
    """
    座位列表查询测试
    GET /api/v1/studyrooms/{room_id}/seats
    功能: 查询某自习室下的座位列表，含实时占用状态
    权限: 需登录
    """

    def test_list_empty(self, client, student_headers, test_room):
        """
        功能名: 座位列表 - 空列表（无座位时）
        功能简介: 自习室存在但未创建座位，返回空列表
        类型: 正向测试（边界情况）
        URL: GET /api/v1/studyrooms/{room_id}/seats
        测试用例: fixture 新建自习室 test_room（无座位），学生请求座位列表
        预期结果: code=200, data 为空列表
        """
        resp = client.get(
            f'/api/v1/studyrooms/{test_room["room_id"]}/seats',
            headers=student_headers
        )
        data = resp.get_json()
        assert data['code'] == 200
        assert isinstance(data['data'], list)


class TestSeatCreate:
    """
    座位创建测试
    POST /api/v1/studyrooms/{room_id}/seats
    功能: 在指定自习室下创建座位
    权限: 管理员或超级管理员
    """

    def test_create_success(self, client, admin_headers, test_room):
        """
        功能名: 创建座位
        功能简介: 管理员创建带插座的座位
        类型: 正向测试
        URL: POST /api/v1/studyrooms/{room_id}/seats
        测试用例: seat_number=5, has_power=True
        预期结果: code=200, seat_number=5, has_power=True, is_active=True
        """
        resp = client.post(
            f'/api/v1/studyrooms/{test_room["room_id"]}/seats',
            json={'seat_number': 5, 'has_power': True},
            headers=admin_headers
        )
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['seat_number'] == 5
        assert data['data']['has_power'] is True
        assert data['data']['is_active'] is True

    def test_create_default_power(self, client, admin_headers, test_room):
        """
        功能名: 创建座位 - 默认无插座
        功能简介: 只传 seat_number，不传 has_power，验证默认为 False
        类型: 正向测试（默认值）
        URL: POST /api/v1/studyrooms/{room_id}/seats
        测试用例: seat_number=6，不传 has_power
        预期结果: code=200, has_power=False
        """
        resp = client.post(
            f'/api/v1/studyrooms/{test_room["room_id"]}/seats',
            json={'seat_number': 6},
            headers=admin_headers
        )
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['has_power'] is False

    def test_create_duplicate_number(self, client, admin_headers, test_seat):
        """
        功能名: 创建座位 - 编号重复
        功能简介: 同一自习室下创建相同编号的座位，验证唯一性
        类型: 反向测试（业务规则）
        URL: POST /api/v1/studyrooms/{room_id}/seats
        测试用例: 同一 room 下再次创建 seat_number=test_seat 已有编号
        预期结果: code=400, message 含"已存在"
        """
        resp = client.post(
            f'/api/v1/studyrooms/{test_seat["room_id"]}/seats',
            json={'seat_number': test_seat['seat_number']},
            headers=admin_headers
        )
        data = resp.get_json()
        assert data['code'] == 400
        assert '已存在' in data['message']

    def test_create_as_student_forbidden(self, client, student_headers, test_room):
        """
        功能名: 创建座位 - 学生越权
        功能简介: 学生角色尝试创建座位，验证权限控制
        类型: 反向测试（权限不足）
        URL: POST /api/v1/studyrooms/{room_id}/seats
        测试用例: 学生 Token 请求创建座位 seat_number=99
        预期结果: code=403
        """
        resp = client.post(
            f'/api/v1/studyrooms/{test_room["room_id"]}/seats',
            json={'seat_number': 99},
            headers=student_headers
        )
        data = resp.get_json()
        assert data['code'] == 403


class TestSeatDetail:
    """
    座位详情测试
    GET /api/v1/seats/{seat_id}
    功能: 获取单个座位信息
    权限: 需登录
    """

    def test_get_detail(self, client, student_headers, test_seat):
        """
        功能名: 座位详情
        功能简介: 查询存在的座位详情
        类型: 正向测试
        URL: GET /api/v1/seats/{seat_id}
        测试用例: fixture 已创建 test_seat（座位号1, 有插座）
        预期结果: code=200, seat_number=1, has_power=True
        """
        resp = client.get(f'/api/v1/seats/{test_seat["seat_id"]}',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['seat_number'] == 1
        assert data['data']['has_power'] is True

    def test_get_detail_not_found(self, client, student_headers):
        """
        功能名: 座位详情 - 不存在
        功能简介: 查询不存在的座位 ID
        类型: 反向测试（资源不存在）
        URL: GET /api/v1/seats/99999
        测试用例: seat_id=99999
        预期结果: code=404
        """
        resp = client.get('/api/v1/seats/99999', headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestSeatUpdate:
    """
    座位更新测试
    PUT /api/v1/seats/{seat_id}
    功能: 更新座位信息（插座、启用状态等）
    权限: 管理员或超级管理员
    """

    def test_update_has_power(self, client, admin_headers, test_seat):
        """
        功能名: 更新座位 - 修改插座状态
        功能简介: 管理员将座位插座从有改为无
        类型: 正向测试
        URL: PUT /api/v1/seats/{seat_id}
        测试用例: has_power=False
        预期结果: code=200, has_power=False
        """
        resp = client.put(f'/api/v1/seats/{test_seat["seat_id"]}', json={
            'has_power': False
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['has_power'] is False

    def test_update_is_active(self, client, admin_headers, test_seat):
        """
        功能名: 更新座位 - 停用座位
        功能简介: 管理员将座位标记为停用
        类型: 正向测试
        URL: PUT /api/v1/seats/{seat_id}
        测试用例: is_active=False
        预期结果: code=200, is_active=False
        """
        resp = client.put(f'/api/v1/seats/{test_seat["seat_id"]}', json={
            'is_active': False
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['is_active'] is False

    def test_update_seat_number_conflict(self, client, admin_headers,
                                         test_seat, test_seat2):
        """
        功能名: 更新座位 - 编号冲突
        功能简介: 修改座位编号为同一自习室下已有编号
        类型: 反向测试（业务规则）
        URL: PUT /api/v1/seats/{seat_id}
        测试用例: 将 test_seat(座位1) 的编号改为 test_seat2(座位2) 的编号
        预期结果: code=400, message 含"已存在"
        """
        resp = client.put(f'/api/v1/seats/{test_seat["seat_id"]}', json={
            'seat_number': test_seat2['seat_number']
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '已存在' in data['message']

    def test_update_not_found(self, client, admin_headers):
        """
        功能名: 更新座位 - 不存在
        功能简介: 更新不存在的座位 ID
        类型: 反向测试（资源不存在）
        URL: PUT /api/v1/seats/99999
        测试用例: seat_id=99999, has_power=True
        预期结果: code=404
        """
        resp = client.put('/api/v1/seats/99999', json={
            'has_power': True
        }, headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestSeatDelete:
    """
    座位删除测试
    DELETE /api/v1/seats/{seat_id}
    功能: 软删除座位（is_del=1）
    权限: 管理员或超级管理员
    """

    def test_delete_success(self, client, admin_headers, test_seat):
        """
        功能名: 删除座位
        功能简介: 软删除座位后，再次查询返回 404
        类型: 正向测试
        URL: DELETE /api/v1/seats/{seat_id}
        测试用例: 删除 fixture 创建的 test_seat，再 GET 查询
        预期结果: DELETE code=200, 再次 GET code=404
        """
        resp = client.delete(f'/api/v1/seats/{test_seat["seat_id"]}',
                             headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 200

        resp2 = client.get(f'/api/v1/seats/{test_seat["seat_id"]}',
                           headers=admin_headers)
        assert resp2.get_json()['code'] == 404

    def test_delete_not_found(self, client, admin_headers):
        """
        功能名: 删除座位 - 不存在
        功能简介: 删除不存在的座位 ID
        类型: 反向测试（资源不存在）
        URL: DELETE /api/v1/seats/99999
        测试用例: seat_id=99999
        预期结果: code=404
        """
        resp = client.delete('/api/v1/seats/99999', headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestSeatAvailability:
    """
    座位可用时段查询测试
    GET /api/v1/seats/{seat_id}/availability
    功能: 查询指定座位某日的空闲时间段（整点区间），返回全部整点时段及空闲标记
    权限: 需登录
    """

    def test_get_availability_success(self, client, student_headers, test_seat):
        """
        功能名: 座位可用时段
        功能简介: 查询座位当天无预约时的全部可用时段
        类型: 正向测试
        URL: GET /api/v1/seats/{seat_id}/availability?date=YYYY-MM-DD
        测试用例: 查询 test_seat 今日可用时段（无预约）
        预期结果: code=200, slots 数组非空, 每项含 start/end/free, 全部 free=True
        """
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        resp = client.get(
            f'/api/v1/seats/{test_seat["seat_id"]}/availability?date={today}',
            headers=student_headers
        )
        data = resp.get_json()
        assert data['code'] == 200
        assert 'slots' in data['data']
        assert len(data['data']['slots']) > 0
        for slot in data['data']['slots']:
            assert 'start' in slot
            assert 'end' in slot
            assert 'free' in slot

    def test_availability_all_free_when_empty(self, client, student_headers,
                                               test_seat):
        """
        功能名: 座位可用时段 - 全部空闲
        功能简介: 无任何预约时，所有时段应为空闲状态
        类型: 正向测试
        URL: GET /api/v1/seats/{seat_id}/availability?date=YYYY-MM-DD
        测试用例: 查询无预约的 test_seat 今日时段
        预期结果: 所有 slot.free 均为 True
        """
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        resp = client.get(
            f'/api/v1/seats/{test_seat["seat_id"]}/availability?date={today}',
            headers=student_headers
        )
        data = resp.get_json()
        for slot in data['data']['slots']:
            assert slot['free'] is True

    def test_availability_seat_not_found(self, client, student_headers):
        """
        功能名: 座位可用时段 - 座位不存在
        功能简介: 查询不存在的座位的可用时段
        类型: 反向测试（资源不存在）
        URL: GET /api/v1/seats/99999/availability
        测试用例: seat_id=99999
        预期结果: code=404
        """
        resp = client.get('/api/v1/seats/99999/availability',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 404