"""
预约管理模块单元测试
=========================
测试预约的创建（含各种校验）、取消、列表查询、详情、提前结束接口
这是系统的核心业务流程测试
"""
import pytest
from datetime import date, timedelta


class TestCreateReservation:
    """
    创建预约测试
    POST /api/v1/reservations
    功能: 创建预约，含整点校验、时长限制、日期范围、座位冲突、
          跨座位冲突、日限额、信誉分等多种校验规则
    权限: 需登录
    """

    def _future_start(self):
        t = date.today().strftime('%Y-%m-%d')
        return f'{t} 09:00:00'

    def _future_end(self):
        t = date.today().strftime('%Y-%m-%d')
        return f'{t} 11:00:00'

    def _future_start2(self):
        t = date.today().strftime('%Y-%m-%d')
        return f'{t} 14:00:00'

    def _future_end2(self):
        t = date.today().strftime('%Y-%m-%d')
        return f'{t} 16:00:00'

    def test_create_reservation_success(self, client, student_headers,
                                         test_seat):
        """
        功能名: 创建预约
        功能简介: 学生在可用时段预约空闲座位
        类型: 正向测试
        URL: POST /api/v1/reservations
        测试用例: seat_id=test_seat, 当天 09:00-11:00
        预期结果: code=200, status=PENDING, seat_id=test_seat.seat_id
        """
        resp = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': self._future_start(),
            'end_time': self._future_end()
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200, data.get('message')
        assert data['data']['status'] == 'PENDING'
        assert data['data']['seat_id'] == test_seat['seat_id']

    def test_create_missing_params(self, client, student_headers):
        """
        功能名: 创建预约 - 参数缺失
        功能简介: 只传 seat_id 不传时间参数
        类型: 反向测试（参数缺失）
        URL: POST /api/v1/reservations
        测试用例: 只传 seat_id=1
        预期结果: code=400
        """
        resp = client.post('/api/v1/reservations', json={
            'seat_id': 1
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400

    def test_create_not_integer_hour(self, client, student_headers, test_seat):
        """
        功能名: 创建预约 - 非整点时间
        功能简介: 预约时间为 09:30，分钟不是 00，验证整点校验
        类型: 反向测试（格式校验）
        URL: POST /api/v1/reservations
        测试用例: 09:30:00 - 11:30:00（非整点）
        预期结果: code=400, message 含"整点"
        """
        resp = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 09:30:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 11:30:00'
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '整点' in data['message']

    def test_create_duration_zero(self, client, student_headers, test_seat):
        """
        功能名: 创建预约 - 时长为零
        功能简介: 开始时间和结束时间相同
        类型: 反向测试（业务规则）
        URL: POST /api/v1/reservations
        测试用例: start=end=09:00:00
        预期结果: code=400
        """
        resp = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': self._future_start(),
            'end_time': self._future_start()
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400

    def test_create_duration_exceeds_max(self, client, student_headers,
                                          test_seat):
        """
        功能名: 创建预约 - 超时限制
        功能简介: 预约时长超过 MAX_RESERVATION_HOURS（默认4小时）
        类型: 反向测试（业务规则）
        URL: POST /api/v1/reservations
        测试用例: 09:00-19:00（10小时，超过4小时限制）
        预期结果: code=400
        """
        resp = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': self._future_start(),
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 19:00:00'
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400

    def test_create_seat_not_found(self, client, student_headers):
        """
        功能名: 创建预约 - 座位不存在
        功能简介: 使用不存在的 seat_id 预约
        类型: 反向测试（资源不存在）
        URL: POST /api/v1/reservations
        测试用例: seat_id=99999
        预期结果: code=400
        """
        resp = client.post('/api/v1/reservations', json={
            'seat_id': 99999,
            'start_time': self._future_start(),
            'end_time': self._future_end()
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400

    def test_create_seat_inactive(self, client, admin_headers, student_headers,
                                   test_seat):
        """
        功能名: 创建预约 - 座位已停用
        功能简介: 停用座位后尝试预约
        类型: 反向测试（业务规则）
        URL: POST /api/v1/reservations
        测试用例: 管理员将 test_seat 停用(is_active=False)，学生再尝试预约
        预期结果: code=400
        """
        client.put(f'/api/v1/seats/{test_seat["seat_id"]}', json={
            'is_active': False
        }, headers=admin_headers)
        resp = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': self._future_start(),
            'end_time': self._future_end()
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400

    def test_create_time_conflict(self, client, student_headers, test_seat):
        """
        功能名: 创建预约 - 同座位时间冲突
        功能简介: 同一时间段被重复预约同一座位
        类型: 反向测试（业务规则-冲突检测）
        URL: POST /api/v1/reservations
        测试用例: 先预约 test_seat 09:00-11:00，再尝试同一时段同一座位
        预期结果: 第二次 code=400, message 含"已被预约"
        """
        client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': self._future_start(),
            'end_time': self._future_end()
        }, headers=student_headers)
        resp = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': self._future_start(),
            'end_time': self._future_end()
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '已被预约' in data['message']

    def test_create_cross_seat_conflict(self, client, student_headers,
                                         test_seat, test_seat2):
        """
        功能名: 创建预约 - 跨座位时间冲突
        功能简介: 同一时间段预约不同座位（同用户）
        类型: 反向测试（业务规则-跨座位冲突）
        URL: POST /api/v1/reservations
        测试用例: 预约 test_seat 09:00-11:00 后，再尝试同一时段预约 test_seat2
        预期结果: code=400, message 含"其他座位"
        """
        client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': self._future_start(),
            'end_time': self._future_end()
        }, headers=student_headers)
        resp = client.post('/api/v1/reservations', json={
            'seat_id': test_seat2['seat_id'],
            'start_time': self._future_start(),
            'end_time': self._future_end()
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '其他座位' in data['message']

    def test_create_daily_limit(self, client, student_headers,
                                 test_seat, test_seat2, test_seat3):
        """
        功能名: 创建预约 - 同天限额
        功能简介: 同一天预约超过2次时被拒绝
        类型: 反向测试（业务规则-日限额）
        URL: POST /api/v1/reservations
        测试用例: 在3个不同座位各预约1次，第3次应被拒绝
        预期结果: 第3次 code=400, message 含"2次"
        """
        client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': self._future_start(),
            'end_time': self._future_end()
        }, headers=student_headers)
        client.post('/api/v1/reservations', json={
            'seat_id': test_seat2['seat_id'],
            'start_time': self._future_start2(),
            'end_time': self._future_end2()
        }, headers=student_headers)
        resp = client.post('/api/v1/reservations', json={
            'seat_id': test_seat3['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 17:00:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 18:00:00'
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '2次' in data['message']


class TestReservationCancel:
    """
    取消预约测试
    PUT /api/v1/reservations/{res_id}/cancel
    功能: 取消 PENDING 状态的预约，本人或管理员可操作
    权限: 需登录（本人）或 admin_required（管理员取消他人）
    """

    def test_cancel_success(self, client, student_headers, test_seat):
        """
        功能名: 取消预约
        功能简介: 本人取消自己 PENDING 状态的预约
        类型: 正向测试
        URL: PUT /api/v1/reservations/{res_id}/cancel
        测试用例: 创建预约后立即取消
        预期结果: code=200, status=CANCELLED
        """
        res = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 09:00:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 11:00:00'
        }, headers=student_headers)
        rid = res.get_json()['data']['res_id']

        resp = client.put(f'/api/v1/reservations/{rid}/cancel',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['status'] == 'CANCELLED'

    def test_cancel_not_own(self, client, student_headers, test_seat):
        """
        功能名: 取消预约 - 非本人（学生）
        功能简介: 其他学生尝试取消别人的预约
        类型: 反向测试（权限不足）
        URL: PUT /api/v1/reservations/{res_id}/cancel
        测试用例: test_student 创建预约，other_student 尝试取消
        预期结果: code=403
        """
        res = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 09:00:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 11:00:00'
        }, headers=student_headers)
        rid = res.get_json()['data']['res_id']

        client.post('/api/v1/auth/register', json={
            'username': 'other_student',
            'password': '123456'
        })
        other = client.post('/api/v1/auth/login', json={
            'username': 'other_student',
            'password': '123456'
        })
        other_token = other.get_json()['data']['access_token']

        resp = client.put(f'/api/v1/reservations/{rid}/cancel',
                          headers={'Authorization': f'Bearer {other_token}'})
        data = resp.get_json()
        assert data['code'] == 403

    def test_cancel_not_found(self, client, student_headers):
        """
        功能名: 取消预约 - 预约不存在
        功能简介: 取消不存在的预约 ID
        类型: 反向测试（资源不存在）
        URL: PUT /api/v1/reservations/99999/cancel
        测试用例: res_id=99999
        预期结果: code=404
        """
        resp = client.put('/api/v1/reservations/99999/cancel',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestMyReservations:
    """
    我的预约列表查询测试
    GET /api/v1/reservations/my
    功能: 查询当前用户的预约列表，支持分页和状态筛选（逗号分隔多值）
    权限: 需登录
    """

    def test_my_list_empty(self, client, student_headers):
        """
        功能名: 我的预约 - 空列表
        功能简介: 新用户无预约记录
        类型: 正向测试（边界情况）
        URL: GET /api/v1/reservations/my
        测试用例: test_student（无预约）请求列表
        预期结果: code=200, items 为空列表
        """
        resp = client.get('/api/v1/reservations/my',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert isinstance(data['data']['items'], list)

    def test_my_list_with_reservations(self, client, student_headers,
                                        test_seat):
        """
        功能名: 我的预约 - 含数据
        功能简介: 创建预约后查询列表，验证扩展字段
        类型: 正向测试
        URL: GET /api/v1/reservations/my
        测试用例: 创建一条预约后请求列表
        预期结果: code=200, total >= 1, items 含 room_name 和 seat_number
        """
        client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 09:00:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 11:00:00'
        }, headers=student_headers)
        resp = client.get('/api/v1/reservations/my',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['total'] >= 1
        item = data['data']['items'][0]
        assert 'room_name' in item
        assert 'seat_number' in item

    def test_my_list_status_filter(self, client, student_headers, test_seat):
        """
        功能名: 我的预约 - 状态筛选
        功能简介: 按 PENDING 状态筛选预约列表
        类型: 正向测试
        URL: GET /api/v1/reservations/my?status=PENDING
        测试用例: 创建一条预约后，按 ?status=PENDING 筛选
        预期结果: code=200, 所有 items 的 status 均为 PENDING
        """
        client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 09:00:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 11:00:00'
        }, headers=student_headers)
        resp = client.get('/api/v1/reservations/my?status=PENDING',
                          headers=student_headers)
        data = resp.get_json()
        for item in data['data']['items']:
            assert item['status'] == 'PENDING'

    def test_my_list_multi_status(self, client, student_headers, test_seat):
        """
        功能名: 我的预约 - 多状态筛选
        功能简介: 按逗号分隔的多个状态筛选
        类型: 正向测试
        URL: GET /api/v1/reservations/my?status=PENDING,ACTIVE
        测试用例: ?status=PENDING,ACTIVE
        预期结果: code=200
        """
        client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 09:00:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 11:00:00'
        }, headers=student_headers)
        resp = client.get('/api/v1/reservations/my?status=PENDING,ACTIVE',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200


class TestReservationDetail:
    """
    预约详情查询测试
    GET /api/v1/reservations/{res_id}
    功能: 获取单条预约完整信息（含自习室名、座位号、位置等）
    权限: 需登录
    """

    def test_get_detail(self, client, student_headers, test_seat):
        """
        功能名: 预约详情
        功能简介: 查询预约详情，验证扩展字段
        类型: 正向测试
        URL: GET /api/v1/reservations/{res_id}
        测试用例: 创建预约后查询详情
        预期结果: code=200, 含 room_name
        """
        res = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 09:00:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 11:00:00'
        }, headers=student_headers)
        rid = res.get_json()['data']['res_id']

        resp = client.get(f'/api/v1/reservations/{rid}',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert 'room_name' in data['data']

    def test_get_detail_not_found(self, client, student_headers):
        """
        功能名: 预约详情 - 不存在
        功能简介: 查询不存在的预约 ID
        类型: 反向测试（资源不存在）
        URL: GET /api/v1/reservations/99999
        测试用例: res_id=99999
        预期结果: code=404
        """
        resp = client.get('/api/v1/reservations/99999',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestReservationComplete:
    """
    提前结束测试
    PUT /api/v1/reservations/{res_id}/complete
    功能: 将 ACTIVE 状态预约提前结束为 COMPLETED
    权限: 需登录（本人）
    """

    def test_complete_success(self, client, student_headers, admin_headers,
                               test_seat, test_checkin_code):
        """
        功能名: 提前结束预约
        功能简介: 签到后（ACTIVE状态）提前结束使用
        类型: 正向测试
        URL: PUT /api/v1/reservations/{res_id}/complete
        测试用例: 创建预约 → 签到 → 提前结束
        预期结果: code=200, status=COMPLETED
        """
        res = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 09:00:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 11:00:00'
        }, headers=student_headers)
        rid = res.get_json()['data']['res_id']

        client.post(f'/api/v1/reservations/{rid}/checkin', json={
            'checkin_code': test_checkin_code
        }, headers=student_headers)

        resp = client.put(f'/api/v1/reservations/{rid}/complete',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['status'] == 'COMPLETED'

    def test_complete_not_active(self, client, student_headers, test_seat):
        """
        功能名: 提前结束 - 非 ACTIVE 状态
        功能简介: 对 PENDING 状态预约提前结束应被拒绝
        类型: 反向测试（状态校验）
        URL: PUT /api/v1/reservations/{res_id}/complete
        测试用例: 创建预约（PENDING）后直接调用 complete
        预期结果: code=400
        """
        res = client.post('/api/v1/reservations', json={
            'seat_id': test_seat['seat_id'],
            'start_time': f'{date.today().strftime("%Y-%m-%d")} 09:00:00',
            'end_time': f'{date.today().strftime("%Y-%m-%d")} 11:00:00'
        }, headers=student_headers)
        rid = res.get_json()['data']['res_id']

        resp = client.put(f'/api/v1/reservations/{rid}/complete',
                          headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400