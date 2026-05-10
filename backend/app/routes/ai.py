from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

ai_bp = Blueprint('ai', __name__)

FAQ_RESPONSES = {
    '签到': '请在预约开始时间后，在座位所在自习室屏幕上获取签到码，输入或扫码完成签到。',
    '预约': '在自习室详情页选择空闲座位，选择连续空闲时间段（整点小时块），点击预约即可。',
    '取消': '在"我的预约"中找到待签到状态的预约，点击取消即可。',
    '违约': '预约开始后15分钟内未签到将被记为违约，扣除信誉分。信誉分过低可能影响预约资格。',
    '开放时间': '自习室通常开放时间为07:00-22:00，具体以各自习室公告为准。',
    '座位': '单击自习室查看座位列表，绿色表示空闲，红色表示已占用。有插座标识的座位可充电。',
    '注册': '请使用学号/工号作为用户名，填写邮箱完成注册，初始信誉分100。',
}


# ============================================================
# POST /api/v1/ai/ask
# 功能: 智能问答（基于关键词匹配FAQ）
# 权限: 需登录（JWT Token）
# 请求头: Authorization: Bearer <access_token>
# 请求体 JSON:
#   { "question": "如何签到？" }   // 必填，用户问题
# 返回: { "answer": "请在预约开始时间后..." }
# 注: 匹配关键字：签到、预约、取消、违约、开放时间、座位、注册
#     未匹配时返回通用帮助提示
# ============================================================
@ai_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask():
    data = request.get_json()
    question = data.get('question', '')

    if not question:
        return jsonify({'code': 400, 'message': '请输入问题', 'data': None}), 400

    answer = None
    for keyword, response in FAQ_RESPONSES.items():
        if keyword in question:
            answer = response
            break

    if not answer:
        answer = '您好，关于您的问题，建议查阅系统帮助文档或联系管理员。常见问题包括：签到、预约、取消、违约、座位、开放时间等。'

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {'answer': answer}
    })