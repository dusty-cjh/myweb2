import re
import sys
import asyncio as aio
import xmltodict as xml
from datetime import datetime
from django.http.request import HttpRequest
from asgiref.sync import async_to_sync as a2s, sync_to_async as s2a
from mybot.models import AbstractOneBotEventHandler, UserProfile as Profile, AsyncJobConfig, AsyncJob
from mybot.onebot.serializers import RequestGroupResponse, RequestGroupRequest, RequestFriendResponse
from mybot.onebot.apis import get_session
from mybot.event_loop import get_message, call
from mybot.onebot_apis import OneBotApi
from mybot import event_loop

PLUGIN_NAME = '自动通过'
YSU_GROUP = [1143835437, 645125440, 1127243020]

MSG_NOTI = """注意！
本消息为Ji器人例行公事，非真人

你可以直接留言，管理员看到会回复"""
MSG_REQUIRE_USER_INFO = """hello,
我是{group_name}的群管理

为防止营销号、广告进入，
本群已开启实名认证

请回复我：姓名+学号，
例：202011010704，赵险峰

2min 内验证失败将踢出群聊呦~"""
MSG_ERR_NO_SCHOOL_ID = '您所发的消息不含学号！请重新发送\n例：202011010704，赵险峰'
MSG_ERR_RETRY = '验证失败！\n你还有一次重试机会'
MSG_ERR_VERIFY_FAILED = '验证失败！'
MSG_SUCCESS = '验证成功！\n祝您冲浪愉快~\n\n❤️觉得我做的还不错的话，可以加个好友呦～'
MSG_FAILED = 'Validation failed\nwatch out your ass'
MSG_VERIFICATION_MESSAGE_INVALID = '姓名或学号不正确，请重新输入\n（机器人自动验证）'
MSG_ERR_SYSTEM = lambda err: f'系统错误！\n{err}'
MSG_ERR_STUDENT_NUMBER_HAS_BEEN_BOUND = lambda x: f'学号 {x} 已与其他 QQ 进行绑定\n⚠️如非本人操作，请稍后联系群管理员。'

ASYNC_JOB_NAME = 'auto_approve.ysu_check'
NORMAL_ERROR = Exception('auto_approve.normal_error')


class OneBotEventHandler(AbstractOneBotEventHandler):
    reg_school_id = re.compile(r'\d{12}')

    async def event_request_friend(self, event, *args, **kwargs):
        self.log.data('approve {} add {} as friend: {}', event.user_id, event.self_id, event.comment)
        event_loop.call(OneBotApi.send_private_msg(user_id=event.user_id, message=MSG_NOTI))
        resp = {
            'approve': True,
            'remark': datetime.now().strftime('%y/%m/%d %H:%M'),
        }
        return resp

    async def event_request_group_add(self, event, *args, **kwargs):
        if event.group_id in YSU_GROUP:
            # check whether verification message contain school id
            s = self.reg_school_id.search(event.comment)
            if s and s.group():
                profile, err = await get_or_create_user_info(event.comment, event.user_id, s.group())
                if err == MSG_ERR_VERIFY_FAILED:
                    return RequestGroupResponse({
                        'approve': False,
                        'reason': MSG_VERIFICATION_MESSAGE_INVALID,
                    })
            else:
                await s2a(insert_ysu_check_task)(event.user_id, event.group_id)

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
        resp, err = await get_message(user_id=user_id, timeout=120)
        if err:
            return None, None, err
        message = resp.message
        s = reg.search(message)
        if not s or not s.group():
            await OneBotApi.send_private_msg(user_id=user_id, message=MSG_ERR_NO_SCHOOL_ID)
        else:
            return s.group(), message, None


async def get_or_create_user_info(message: str, qq_number: int, college_student_number: str, college='YSU'):
    # global
    loop = aio.get_running_loop()

    # check whether user has bound other qq number
    profile = await loop.run_in_executor(None, Profile.get_by_student_number, (
        college_student_number,
        college,
    ))
    if profile:
        if profile.qq_number != qq_number:
            return None, MSG_ERR_STUDENT_NUMBER_HAS_BEEN_BOUND(college_student_number)
        else:
            return profile, None

    # get user name
    username = await get_username_by_school_id(college_student_number)
    if not username or username not in message:
        return None, MSG_ERR_VERIFY_FAILED

    # create user info
    ret = await s2a(Profile.objects.create, thread_sensitive=True)(
        name=username,
        qq_number=qq_number,
        college='YSU',
        college_student_number=college_student_number,
    )
    return ret, None


async def ysu_check(user_id: int, group_id=None, job_id=None):
    print('[ysu_check] start', file=sys.stderr)
    # send noti
    await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=MSG_NOTI)
    await aio.sleep(3)
    ret = await OneBotApi.send_private_msg(
        user_id=user_id,
        group_id=group_id,
        message=MSG_REQUIRE_USER_INFO.format(group_name=OneBotApi.get_group_info(group_id)['group_name']),
    )
    print('[ysu_check] request user info', ret, file=sys.stderr)

    # get user info
    success = False
    for i in range(2):
        school_id, message, err = await get_school_id(user_id, group_id)
        if err:
            break
        profile, err = await get_or_create_user_info(message, user_id, school_id)
        if err:
            # whether could retry
            if err == MSG_ERR_VERIFY_FAILED:
                if i <= 1:
                    await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=MSG_ERR_RETRY)
                else:
                    await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=MSG_ERR_SYSTEM(err))
        else:
            success = True
            break

    # kick out if validate fail
    if not success:
        if group_id:
            await OneBotApi.set_group_kick(user_id=user_id, group_id=group_id, reject_add_request=False)
        else:
            await OneBotApi.send_private_msg(user_id=user_id, message=MSG_FAILED)
    else:
        for msg in MSG_SUCCESS.split('\n\n'):
            await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=msg)

    print('[ysu_check] end', file=sys.stderr)
    if job_id:
        await s2a(AsyncJob.set_result_by_id)(job_id, {
            'user_id': user_id,
            'group_id': group_id,
            'result': success,
        }, AsyncJob.STATUS_SUCCESS)


def ysu_check_job_handler(job: AsyncJob):
    params = job.parse_params()
    user_id = params['user_id']
    group_id = params['group_id']
    event_loop.call(ysu_check(user_id, group_id))
    return NORMAL_ERROR


def insert_ysu_check_task(user_id: int, group_id: int) -> AsyncJob:
    job = AsyncJob.insert(ASYNC_JOB_NAME, dict(locals()))
    return job


AsyncJobConfig.objects.get_or_create(
    job_name=ASYNC_JOB_NAME,
    handler=ysu_check_job_handler,
)
