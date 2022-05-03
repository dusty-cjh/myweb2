import re
import sys

import xmltodict as xml
from datetime import datetime
from django.http.request import HttpRequest
from mybot.models import AbstractOneBotEventHandler
from mybot.onebot.serializers import RequestGroupResponse, RequestGroupRequest, RequestFriendResponse
from mybot.onebot.apis import get_session
from mybot.event_loop import get_message
from mybot.onebot_apis import OneBotApi
from mybot import event_loop

PLUGIN_NAME = '自动通过'
YSU_GROUP = [1143835437, 645125440, 1127243020]

MSG_NOTI = """注意！
本消息为Ji器人例行公事，非真人。

你可以直接留言，管理员看到会回复。"""
MSG_REQUIRE_USER_INFO = """hello,
我是{group_name}的群管理。

为防止营销号、广告进入，
本群已开启实名认证。

请回复我：姓名+学号，
例如：202011010704，李小明

10min 内验证失败将踢出群聊呦~"""
MSG_ERR_NO_SCHOOL_ID = '您所发的消息不含学号！请重新发送'
MSG_ERR_RETRY = '验证失败！\n你还有一次重试机会'
MSG_SUCCESS = '验证成功！\n祝您冲浪愉快~'


class OneBotEventHandler(AbstractOneBotEventHandler):
    async def event_request_friend(self, event, *args, **kwargs):
        self.log.data('approve {} add {} as friend: {}', event.user_id, event.self_id, event.comment)
        resp = {
            'approve': True,
            'remark': datetime.now().strftime('%y/%m/%d %H:%M'),
        }
        return resp

    async def event_request_group_add(self, event, *args, **kwargs):
        print('event_request_group_add', event.self_id, event.user_id, event.group_id, event.comment)
        if event.group_id in YSU_GROUP:
            event_loop.call(ysu_check(event.user_id, event.group_id))

        self.log.data('{} approve {} to join group {}: {}', event.self_id, event.user_id, event.group_id, event.comment)
        resp = RequestGroupResponse({
            'approve': True,
            'reason': '',
        })
        return resp

    async def event_request_group_invite(self, event, *args, **kwargs):
        self.log.data('{} agree {}\'s invitation of join group {}', event.self_id, event.user_id, event.group_id)
        resp = RequestGroupResponse({
            'approve': True,
            'reason': '',
        })
        return resp


async def get_username_by_school_id(school_id: str):
    # validate input data
    if len(school_id) != 12:
        return None

    # construct http request
    data = 'word=%s&index=4&currentPage=1&sql=stuSql&building=undefined&srtp_teacher_project_num=undefined&planyear=undefined' % school_id
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # get response
    async with get_session() as session:
        async with session.post('http://202.206.243.8/StuExpbook/AutoCompleteServletSrtp',
                                data=data, headers=headers) as resp:
            if resp.status != 200:
                raise AssertionError('ysu-campus-server response status error: %d' % resp.status)
            data = await resp.text(encoding='utf8')

    # parse response
    data = xml.parse(data)
    data = data['words'].get('word')
    if data:
        if isinstance(data, str):
            _id, name = data.split('-')
            return name
        elif isinstance(data, list):
            data = [x.split('-') for x in data]
            id_to_name = {x[0]: x[1] for x in data}
            return id_to_name.get(school_id)


async def get_school_id(user_id: int, group_id):
    reg = re.compile(r'\d{12}')
    while True:
        message = await get_message(user_id=user_id, group_id=group_id, timeout=600)
        s = reg.search(message)
        if not s or not s.group():
            await OneBotApi.send_private_msg(user_id=user_id, message=MSG_ERR_NO_SCHOOL_ID)
        else:
            return s.group(), message


async def ysu_check(user_id: int, group_id):
    print('[ysu_check] start', file=sys.stderr)
    # send noti
    await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=MSG_NOTI)
    ret = await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=MSG_REQUIRE_USER_INFO)
    print('[ysu_check] request user info', ret, file=sys.stderr)

    # get user info
    for _ in range(2):
        school_id, message = await get_school_id(user_id, group_id)
        username = await get_username_by_school_id(school_id)
        if username not in message:
            await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=MSG_ERR_RETRY)
        else:
            await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=MSG_SUCCESS)
            break

    print('[ysu_check] end', file=sys.stderr)
