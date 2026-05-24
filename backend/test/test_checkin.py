"""
签到模块单元测试
=========================
测试签到码生成、刷新、用户签到流程（含状态流转、权限校验、信誉分增减）
"""
import pytest
from datetime import date


class TestGetCheckinCode:
    """
    获取签到码测试
    GET /api/v1/studyrooms/{room_id}/checkin-code
    功能: 获取指定自习室当日签到码，不存在则自动生成6位随机码
    权限: 需登录
    """

    def test_get_code_auto_generate(self, client, admin_headers, test_room):
        """
        功能名: 获取签到码 - 自动生成
        功能简介: 当日签到码不存在时自动生成
        类型: 正向测试
        URL: GET /api/v1/studyrooms/{room_id}/checkin-code
        测试用例: 请求 test_room 今日签到码（数据库中尚无）
        预期结果: code=200, checkin_code 长度为6
        """
        resp = client.get(
            f'/api/v1/studyrooms/{test_room["room_id"]}/checkin-code',
            headers=admin_headers
        )
        data = resp.get_json()
        assert data['code'] == 200
        assert 'checkin_code' in data['data']
        assert len(data['data']['checkin_code']) == 6

    def test_get_code_room_not_found(self, client, admin_headers):
        """
        功能名: 获取签到码 - 自习室不存在
        功能简介: 请求不存在自习室的签到码
        类型: 反向测试（资源不存在）
        URL: GET /api/v1/studyrooms/99999/checkin-code
        测试用例: room_id=99999
        预期结果: code=404
        """
        resp = client.get('/api/v1/studyrooms/99999/checkin-code',
                          headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404

    def test_get_code_specific_date(self, client, admin_headers, test_room):
        """
        功能名: 获取签到码 - 指定日期
        功能简介: 查询未来某日的签到码（自动生成）
        类型: 正向测试
        URL: GET /api/v1/studyrooms/{room_id}/checkin-code?date=2026-06-15
        测试用例: ?date=2026-06-15
        预期结果: code=200, code_date="2026-06-15"
        """
        resp = client.get(
            f'/api/v1/studyrooms/{test_room["room_id"]}/checkin-code?date=2026-06-15',
            headers=admin_headers
        )
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['code_date'] == '2026-06-15'

    def test_get_code_invalid_date(self, client, admin_headers, test_room):
        """
        功能名: 获取签到码 - 无效日期
        功能简介: 传入无法解析的日期格式
        类型: 反向测试（参数格式错误）
        URL: GET /api/v1/studyrooms/{room_id}/checkin-code?date=bad
        测试用例: ?date=bad
        预期结果: code=400
        """
        resp = client.get(
            f'/api/v1/studyrooms/{test_room["room_id"]}/checkin-code?date=bad',
            headers=admin_headers
        )
        data = resp.get_json()
        assert data['code'] == 400


class TestRefreshCheckinCode:
    """
    刷新签到码测试
    POST /api/v1/studyrooms/{room_id}/checkin-code/refresh
    功能: 强制重新生成当日签到码（用于安全刷新）
    权限: 需登录
    """

    def test_refresh_code(self, client, admin_headers, test_room):
        """
        功能名: 刷新签到码
        功能简介: 强制刷新今日签到码
        类型: 正向测试
        URL: POST /api/v1/studyrooms/{room_id}/checkin-code/refresh
        测试用例: 先获取签到码，再刷新
        预期结果: code=200, 新签到码长度6
        """
        client.get(
            f'/api/v1/studyrooms/{test_room["room_id"]}/checkin-code',
            headers=admin_headers
        )
        resp2 = client.post(
            f'/api/v1/studyrooms/{test_room["room_id"]}/checkin-code/refresh',
            headers=admin_headers
        )
        data = resp2.get_json()
        assert data['code'] == 200
        assert len(data['data']['checkin_code']) == 6

    def test_refresh_code_room_not_found(self, client, admin_headers):
        """
        功能名: 刷新签到码 - 自习室不存在
        功能简介: 对不存在的自习室刷新签到码
        类型: 反向测试（资源不存在）
        URL: POST /api/v1/studyrooms/99999/checkin-code/refresh
        测试用例: room_id=99999
        预期结果: code=404
        """
        resp = client.post('/api/v1/studyrooms/99999/checkin-code/refresh',
                           headers=admin_headers)
        data = resp.get_json()
        assert data['code'] == 404


class TestCheckinFlow:
    """
    签到完整流程测试
    POST /api/v1/reservations/{res_id}/checkin
    功能: 使用签到码将 PENDING 预约转为 ACTIVE，签到成功信誉分+5
    权限: 需登录（本人）
    """

    def _make_reservation(self, client, headers, seat_id):
        """辅助方法：创建一条测试预约"""
        t = date.today().strftime('%Y-%m-%d')
        now = '09:00'
        later = '11:00'
        return client.post('/api/v1/reservations', json={
            'seat_id': seat_id,
            'start_time': f'{t} {now}:00',
            'end_time': f'{t} {later}:00'
        }, headers=headers).get_json()['data']['res_id']

    def test_checkin_success(self, client, student_headers, test_seat,
                              test_checkin_code):
        """
        功能名: 用户签到
        功能简介: 使用正确的签到码签到，状态从 PENDING 变为 ACTIVE
        类型: 正向测试
        URL: POST /api/v1/reservations/{res_id}/checkin
        测试用例: 创建预约 → 使用有效签到码签到
        预期结果: code=200, status=ACTIVE
        """
        rid = self._make_reservation(client, student_headers,
                                      test_seat['seat_id'])
        resp = client.post(f'/api/v1/reservations/{rid}/checkin', json={
            'checkin_code': test_checkin_code
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 200, data.get('message')
        assert data['data']['status'] == 'ACTIVE'

    def test_checkin_wrong_code(self, client, student_headers, test_seat):
        """
        功能名: 签到 - 签到码错误
        功能简介: 使用错误的签到码签到
        类型: 反向测试（校验失败）
        URL: POST /api/v1/reservations/{res_id}/checkin
        测试用例: checkin_code="WRONG1"
        预期结果: code=400, message 含"错误"
        """
        rid = self._make_reservation(client, student_headers,
                                      test_seat['seat_id'])
        resp = client.post(f'/api/v1/reservations/{rid}/checkin', json={
            'checkin_code': 'WRONG1'
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400
        assert '错误' in data['message']

    def test_checkin_not_own(self, client, student_headers, test_seat,
                              test_checkin_code):
        """
        功能名: 签到 - 非本人
        功能简介: 尝试替其他用户签到
        类型: 反向测试（权限不足）
        URL: POST /api/v1/reservations/{res_id}/checkin
        测试用例: test_student 创建预约，checkin_other 用户尝试签到
        预期结果: code=403
        """
        rid = self._make_reservation(client, student_headers,
                                      test_seat['seat_id'])
        client.post('/api/v1/auth/register', json={
            'username': 'checkin_other',
            'password': '123456'
        })
        other = client.post('/api/v1/auth/login', json={
            'username': 'checkin_other',
            'password': '123456'
        })
        other_token = other.get_json()['data']['access_token']

        resp = client.post(f'/api/v1/reservations/{rid}/checkin', json={
            'checkin_code': test_checkin_code
        }, headers={'Authorization': f'Bearer {other_token}'})
        data = resp.get_json()
        assert data['code'] == 403

    def test_checkin_reservation_not_found(self, client, student_headers):
        """
        功能名: 签到 - 预约不存在
        功能简介: 对不存在的预约签到
        类型: 反向测试（资源不存在）
        URL: POST /api/v1/reservations/99999/checkin
        测试用例: res_id=99999, checkin_code="ABC123"
        预期结果: code=404
        """
        resp = client.post('/api/v1/reservations/99999/checkin', json={
            'checkin_code': 'ABC123'
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 404

    def test_checkin_already_checked_in(self, client, student_headers,
                                         test_seat, test_checkin_code):
        """
        功能名: 签到 - 重复签到
        功能简介: 对已签到（ACTIVE）的预约再次签到
        类型: 反向测试（状态校验）
        URL: POST /api/v1/reservations/{res_id}/checkin
        测试用例: 签到成功后再次对同一预约签到
        预期结果: 第二次 code=400
        """
        rid = self._make_reservation(client, student_headers,
                                      test_seat['seat_id'])
        client.post(f'/api/v1/reservations/{rid}/checkin', json={
            'checkin_code': test_checkin_code
        }, headers=student_headers)
        resp = client.post(f'/api/v1/reservations/{rid}/checkin', json={
            'checkin_code': test_checkin_code
        }, headers=student_headers)
        data = resp.get_json()
        assert data['code'] == 400

    def test_checkin_increases_credit_score(self, client, student_headers,
                                             test_seat, test_checkin_code):
        """
        功能名: 签到 - 信誉分增加
        功能简介: 签到成功后信誉分应 +5（不超过100）
        类型: 正向测试
        URL: POST /api/v1/reservations/{res_id}/checkin
        测试用例: 签到前获取信誉分 → 创建预约并签到 → 签到后获取信誉分
        预期结果: score_after = min(100, score_before + 5)
        """
        me_before = client.get('/api/v1/auth/me', headers=student_headers)
        score_before = me_before.get_json()['data']['credit_score']

        rid = self._make_reservation(client, student_headers,
                                      test_seat['seat_id'])
        client.post(f'/api/v1/reservations/{rid}/checkin', json={
            'checkin_code': test_checkin_code
        }, headers=student_headers)

        me_after = client.get('/api/v1/auth/me', headers=student_headers)
        score_after = me_after.get_json()['data']['credit_score']
        assert score_after == min(100, score_before + 5)