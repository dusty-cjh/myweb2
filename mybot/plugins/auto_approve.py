import re
import sys
import logging
import asyncio as aio
import xmltodict as xml
from datetime import datetime
from django.http.request import HttpRequest
from django.conf import settings
from asgiref.sync import async_to_sync as a2s, sync_to_async as s2a

from common.logger import Logger
from common.constants import ErrCode, ErrMsg
from common import utils
from post.models import AsyncFuncJob, create_async_coroutine_job
from post.decorators import get_async_job_logger, async_coroutine, AsyncCoroutineFuncContext
from mybot.models import (
    AbstractOneBotEventHandler, OneBotCmdMixin, OneBotEvent, UserProfile as Profile, AbstractOneBotPluginConfig,
    serializer,
)
from mybot.onebot.serializers import RequestGroupResponse, RequestGroupRequest, RequestFriendResponse
from mybot.onebot.apis import get_session
from mybot.event_loop import get_private_message, call
from mybot.onebot_apis import OneBotApi
from mybot import event_loop

logger = Logger('mybot')
counter = utils.new_counter(to_string=True)()
NORMAL_ERROR = Exception('auto_approve.normal_error')


class PluginConfig(AbstractOneBotPluginConfig):
    YSU_GROUP = [1143835437, 645125440, 1127243020]
    MAX_LIFETIME = serializer.IntField(verbose_name='config - task max lifetime', default=60 if settings.DEBUG else 1800)
    # JUMP_HINT = {'研究生', '里仁'}

    MSG_NOTICE_WELCOME = """注意！
本消息为Ji器人例行公事，非真人

你可以直接留言，管理员看到会回复"""
    MSG_NOTICE_WELCOME = serializer.CharField(verbose_name='notice - welcome', default=MSG_NOTICE_WELCOME)

    MSG_RESPONSD_GONNA_PROCESS = serializer.CharField(
        verbose_name='respond - gonna process', default='即将在{group_id}验证{user_id}的燕大身份')

    MSG_NOTICE_GUIDE = """hello,
我是{group_name}的群管理
🌞
为防止营销号、广告进入，
本群已开启实名认证
🍦
请回复我：姓名+学号，
例：123456985211，赵险峰
🌟
10min 内验证失败将踢出群聊呦~"""
    MSG_NOTICE_GUIDE = serializer.CharField(verbose_name='notice - guide', default=MSG_NOTICE_GUIDE)

    CONFIG_REGEXP_YSU_ID = serializer.CharField(verbose_name='config - ysu id regexp', default=r'(1\d{11}|20[12]\d{9})')
    MSG_ERR_INPUT_CONTAINS_NO_ID = serializer.CharField(
        verbose_name='error - input contains no id',
        default='您所发的消息不含学号！请重新发送\n例：123456985211，赵险峰',
    )
    MSG_ERR_VERIFY_HINT = serializer.CharField(verbose_name='error - id and name not match', default='提示：\n{} {}')
    MSG_NOTICE_SUCCESS = serializer.CharField(
        verbose_name='notice - success',
        default='验证成功！\n祝您冲浪愉快~\n\n❤️觉得我做的还不错的话，可以加个好友呦～',
    )
    MSG_NOTICE_PUSH = serializer.CharField(verbose_name='notice - urge', default='🐳宝，请尽快完成验证。\n不然过一会我就踢了呦～')
    MSG_NOTICE_CHECK_LATER = serializer.CharField(verbose_name='notice - check later', default='不是本科生？\n管理员稍后将手动验证')
    MSG_NOTICE_GONNA_KICK_OUT = serializer.CharField(verbose_name='notice - kick out', default='拿稳✈️🎫，一路顺风～\n👋👋')

    verbose_name = serializer.CharField(default='自动通过')


plugin_config = PluginConfig.get_latest()


def msg_err_verify_hint(id, name):
    return plugin_config.MSG_ERR_VERIFY_HINT.format(id, '*' * (len(name) - 1) + name[-1])


class OneBotEventHandler(OneBotCmdMixin, AbstractOneBotEventHandler):

    async def event_request_friend(self, event, *args, **kwargs):
        logger.info('approve {} add {} as friend: {}', event.user_id, event.self_id, event.comment)
        event_loop.call(OneBotApi.send_private_msg(user_id=event.user_id, message=plugin_config.MSG_NOTICE_WELCOME))
        resp = {
            'approve': True,
            'remark': datetime.now().strftime('%y/%m/%d %H:%M'),
        }
        return resp

    async def event_request_group_add(self, event, *args, **kwargs):
        if event.group_id in plugin_config.YSU_GROUP:
            # check whether verification message contain school id
            s = re.search(plugin_config.CONFIG_REGEXP_YSU_ID, event.comment)
            if s and s.group():
                profile, err = await create_user_profile(event.comment, event.user_id, s.group())
                if err:
                    return RequestGroupResponse({
                        'approve': False,
                        'reason': msg_err_verify_hint(s.group(), profile),
                    })

        logger.info('{} approve {} to join group {}: {}', event.self_id, event.user_id, event.group_id, event.comment)
        resp = RequestGroupResponse({
            'approve': True,
            'reason': '',
        })
        return resp

    async def event_request_group_invite(self, event, *args, **kwargs):
        self.log.data('{} agree {}\'s invitation of join group {}', event.self_id, event.user_id, event.group_id)
        logger.info('{} agree {}\'s invitation of join group {}', event.self_id, event.user_id, event.group_id)
        resp = RequestGroupResponse({
            'approve': True,
            'reason': '',
        })
        return resp

    async def event_notice_group_increase_approve(self, event, *args, **kwargs):
        self.log.info('group increase event: {}', event)
        if event.group_id not in plugin_config.YSU_GROUP:
            return

        # # go-cqhttp bug: event.operator_id always is true
        # if event.self_id == event.operator_id:
        #     return

        # user used has been verified
        if await s2a(Profile.objects.filter(qq_number=event.user_id).exclude(certificate=0).exists)():
            return

        job = await ysu_check.add_job(event.user_id, event.group_id)
        self.log.info('added ysu check job: ', job)

    async def cmd_ysu_check(self, e: OneBotEvent, *args, **kwargs):
        # parse params
        user_id = e.user_id
        if len(args) >= 2:
            user_id = args[1]
            group_id = args[2]
        else:
            group_id = self._get_group_id(e)

        # validate
        if not group_id:
            return {
                'reply': ErrCode.INVALID_PARAMETERS.to_errmsg()
            }

        # add job
        await ysu_check.add_job(int(user_id), int(group_id))
        return {
            'reply': plugin_config.MSG_RESPONSD_GONNA_PROCESS.format(group_id=group_id, user_id=user_id)
        }


def mask_username(name):
    return '*' * (len(name) - 1) + name[-1]


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
    while True:
        # get user input
        resp, err = await get_private_message(user_id=user_id, timeout=plugin_config.MAX_LIFETIME)
        if err:
            return None, None, err

        # search ysu id
        message = resp.message
        s = re.search(plugin_config.CONFIG_REGEXP_YSU_ID, message)
        if not s or not s.group():
            await OneBotApi.send_private_msg(user_id=user_id, message=plugin_config.MSG_ERR_INPUT_CONTAINS_NO_ID)
        else:
            return s.group(), message, None


async def create_user_profile(message: str, qq_number: int, college_student_number: str, college='YSU') -> tuple[Profile, int]:
    err = ErrCode.SUCCESS
    username = await get_username_by_school_id(college_student_number)
    profile = dict(
        qq_number=qq_number,
        college=college,
        college_student_number=college_student_number,
    )
    if not username:
        profile['name'] = message
    else:
        if username in message:
            profile['name'] = username
            profile['certificate'] = Profile.CERT_COLLEGE_ID
        else:
            err = ErrCode.VALIDATION_FAILED
            return username, err

    profile = await s2a(Profile.objects.create, thread_sensitive=True)(**profile)
    return profile, err


@async_coroutine(max_lifetime=3600*12)
async def ysu_check(ctx: AsyncCoroutineFuncContext, user_id: int, group_id: int, *args, ysu_info=None, has_noti=False, **kwargs):
    global plugin_config
    plugin_config = await s2a(PluginConfig.get_latest)()

    if not user_id or not group_id:
        raise ValueError('user_id and group_id must be provided')

    ret = {}
    log = ctx.log
    log.info(f'[ysu_check] start, user_id={user_id}, group_id={group_id}')
    if settings.DEBUG:
        print('[ysu_check] start, trace_id=', log.get_trace_id())

    if ysu_info:
        log.info('ysu_id and name not match')
        await OneBotApi.send_private_msg(
            user_id=user_id, group_id=group_id,
            message=msg_err_verify_hint(*ysu_info))
    else:
        # send noti
        if not has_noti:
            await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=plugin_config.MSG_NOTICE_WELCOME)
            await aio.sleep(3)
            resp = await OneBotApi.get_group_info(group_id=group_id)
            if resp['retcode'] != 0:
                log.info('[ysu_check] get_group_info of %d failed' % group_id, file=sys.stderr)
                return

            log.info('remind user to input ysu id and user name')
            group_info = resp['data']
            for msg in plugin_config.MSG_NOTICE_GUIDE.format(group_name=group_info['group_name']).split('\n\n'):
                await OneBotApi.send_private_msg(
                    user_id=user_id,
                    group_id=group_id,
                    message=msg,
                )
            await ctx.update_kwargs(has_noti=True)
        else:
            await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=plugin_config.MSG_NOTICE_PUSH)
            log.info('user has been notified')

    # get user info
    log.info('waiting for user to input correct ysu id')
    school_id, message, err = await get_school_id(user_id, group_id)
    if err:
        if ctx.job.max_retry <= ctx.job.retries:
            log.info('has reach max retry limitation')
            await OneBotApi.send_private_msg(
                user_id=user_id, group_id=group_id, message=plugin_config.MSG_NOTICE_GONNA_KICK_OUT)
            await aio.sleep(3)
            await OneBotApi.set_group_kick(user_id=user_id, group_id=group_id, reject_add_request=False)
            ret['status'] = 'fail'
            ret['reason'] = 'user has reach max retry'
        log.info('get correct ysu id failed, error={}', repr(err))
        raise err

    log.info('get ysu student info from jwc.ysu.edu.cn, user-input: {}', message)
    profile, err = await create_user_profile(message, user_id, school_id)
    if err:
        log.info('ysu_id and name not match')
        await OneBotApi.send_private_msg(
            user_id=user_id, group_id=group_id,
            message=msg_err_verify_hint(school_id, profile))
        await OneBotApi.send_private_msg(
            user_id=user_id, group_id=group_id,
            message='❤️请重新加裙验证{}'.format(group_id)
        )
        await OneBotApi.set_group_kick(user_id=user_id, group_id=group_id, reject_add_request=False)
        ret['err'] = 'ysu id and name not match'
    else:
        # has reach max retry limitation
        if not profile.certificate:
            if ctx.job.max_retry == ctx.job.retries:
                log.info('has reach max retry limitation')
                await OneBotApi.send_private_msg(
                    user_id=user_id, group_id=group_id, message=plugin_config.MSG_NOTICE_GONNA_KICK_OUT)
                await aio.sleep(3)
                await OneBotApi.set_group_kick(user_id=user_id, group_id=group_id, reject_add_request=False)
                ret['status'] = 'fail'
                ret['reason'] = 'user has reach max retry'
                return ret
            else:
                await OneBotApi.send_private_msg(
                    user_id=user_id, group_id=group_id, message=plugin_config.MSG_NOTICE_CHECK_LATER)
                ret['status'] = 'fail'
                ret['reason'] = 'ysu id format right, but user info not found'
                return ret
        else:
            ret['status'] = 'verify success'
            log.info(f'ysu_check success, send success notice to user-{user_id}')
            for msg in plugin_config.MSG_NOTICE_SUCCESS.split('\n\n'):
                await OneBotApi.send_private_msg(user_id=user_id, group_id=group_id, message=msg)

    log.info('[ysu_check] end')
    if settings.DEBUG:
        print('[ysu_check] end, trace_id=', log.get_trace_id(), file=sys.stderr)
    return ret
