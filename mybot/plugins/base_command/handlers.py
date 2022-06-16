import asyncio as aio
import random
from datetime import timedelta
import re
from asgiref.sync import sync_to_async as s2a
from django.db.utils import OperationalError
from django.core.cache import cache
from bridge.onebot import (
    OneBotEvent, CQCode, AsyncOneBotApi, OneBotCmdMixin, Role, PostType,
)
from common import utils
from mybot.models import OneBotEventTab, BaseOneBotEventHandler
from mybot import event_loop
from .settings import PluginConfig, CacheKey


MSG_SUCCESS_KICK = '已踢'
MSG_ERR_INVALID_KICKED_USER_ID = '被踢人QQ号格式错误！'
MSG_ERR_BAD_PERMISSION = '无权操作！'
MSG_ERR_INTERNAL_SERVER_ERROR = '处理出错！请重试'

PLUGIN_NAME = '基本命令'


class OneBotEventHandler(BaseOneBotEventHandler, OneBotCmdMixin):
    cfg: PluginConfig

    async def should_check(self, event: OneBotEvent, *args, **kwargs):
        # auto_approve
        if event.post_type in (PostType.REQUEST, PostType.META_EVENT):
            return True

    async def event_message_private(self, event: OneBotEvent, *args, **kwargs):
        # save all private message to DB
        try:
            await s2a(OneBotEventTab.save_message)(event)
        except OperationalError as e:
            self.log.error('save message to DB failed, err={}, msg={}', e, event)

        return await super().event_message_private(event, *args, **kwargs)

    async def event_message_sent(self, event: OneBotEvent, *args, **kwargs):
        # save all self sent message to DB
        try:
            await s2a(OneBotEventTab.save_message)(event)
        except OperationalError as e:
            self.log.error('save message to DB failed, err={}, msg={}', e, event)

        return await super().event_message(event, *args, **kwargs)

    async def event_message_group_normal(self, event: OneBotEvent, *args, **kwargs):
        if Role.is_manager(event.sender.role):
            # process kick
            if event.raw_message.startswith('kick') or event.raw_message.endswith('kick'):
                ret = await self.process_group_kick(event)
                if ret:
                    return ret

        return await super().event_message_group_normal(event, *args, **kwargs)

    async def process_group_kick(self, event: OneBotEvent):
        api = AsyncOneBotApi()
        success_count = 0
        cq_code_list = CQCode.parse_cq_code_list(event.raw_message)
        for code in filter(lambda code: code.type == 'at', cq_code_list):
            resp, err = await api.with_max_retry(3).set_group_kick(event.group_id, code.data['qq'])
            if err:
                self.log.error('process group kick failed: errcode={}, resp={}', err, resp)
            else:
                success_count += 1
        resp, err = await api.send_group_msg('success kicked %d member' % success_count, event.group_id)
        if err:
            self.log.error('process group kick send group msg failed: errcode={}, resp={}', err, resp)

    async def cmd_kick(self, event: OneBotEvent, *args, **kwargs):
        # check params
        user_id = args[1]
        if not user_id.isdigit():
            return {
                'reply': MSG_ERR_INVALID_KICKED_USER_ID,
            }

        # get info
        group_id = int(args[2]) if len(args) >= 2 else self._get_group_id(event)
        sender_id = event.user_id
        resp = await AsyncOneBotApi().get_group_member_info_with_cache(group_id, sender_id)
        if resp.get('retcode') != 0:
            self.log.error('base_command.cmd_kick|get_group_member_info_with_cache failed|response={}', repr(resp))
            return {
                'reply': MSG_ERR_INTERNAL_SERVER_ERROR,
            }
        user_info = resp.get('data')

        # check permission
        self.log.info(f'{user_id} kick {user_id} from {sender_id}')
        if user_info['role'] not in ('admin', 'owner'):
            return {}

        # kick user
        resp = await AsyncOneBotApi().set_group_kick(
            group_id=group_id,
            user_id=user_id,
        )
        if resp.get('retcode') != 0:
            self.log.error(
                'base_command.cmd_kick|set_group_kick(gid={}, uid={}) failed|response={}',
                group_id,
                user_id,
                repr(resp),
            )
            return {
                'reply': resp.get('wording') or resp.get('msg') or MSG_ERR_INTERNAL_SERVER_ERROR,
            }
        else:
            return {
                'reply': MSG_SUCCESS_KICK,
            }

    async def event_request_friend(self, event: OneBotEvent, *args, **kwargs):
        async def approve(flag, duration):
            await aio.sleep(duration)
            resp, err = await self.api.with_max_retry(3).set_friend_add_request(
                flag,
                remark=utils.get_datetime_now().strftime('%y/%m/%d %H:%M'),
            )
            if err:
                self.log.error('approve friend {} request failed, err={}, resp={}', event.user_id, err, resp)
            else:
                self.log.info('approved {} add {} as friend: {}', event.user_id, event.self_id, event.comment)

        self.log.info('start approve group add request for {}', event.user_id)
        now = utils.get_datetime_now()
        timestamp = await cache.aget(CacheKey.AUTO_APPROVE_FRIEND_ADD, now)
        if timestamp <= now:
            duration = self.cfg.AUTO_APPROVE_FRIEND_ADD_REQUEST
            timestamp = now
        else:
            duration = (timestamp - now).seconds
        event_loop.call(approve(event.flag, duration))
        await cache.aset(
            CacheKey.AUTO_APPROVE_FRIEND_ADD,
            timestamp + timedelta(seconds=self.cfg.AUTO_APPROVE_INTERVAL + random.randint(0, 20)),
        )

        # block propagate
        return {}

    async def event_request_group_add(self, event: OneBotEvent, *args, **kwargs):
        async def approve(flag, duration):
            await aio.sleep(duration)
            resp, err = await self.api.with_max_retry(3).set_group_add_request(flag)
            if err:
                self.log.error('approve group add request failed, err={}, resp={}', err, resp)
            else:
                self.log.info('approved group add request, resp={}', resp)

        self.log.info('start approve group add request for {}', event.user_id)
        now = utils.get_datetime_now()
        timestamp = await cache.aget(CacheKey.AUTO_APPROVE_GRUOP_ADD, now)
        if timestamp <= now:
            duration = self.cfg.AUTO_APPROVE_INTERVAL
            timestamp = now
        else:
            duration = (timestamp - now).seconds
        event_loop.call(approve(event.flag, duration))
        await cache.aset(
            CacheKey.AUTO_APPROVE_GRUOP_ADD,
            timestamp + timedelta(seconds=self.cfg.AUTO_APPROVE_INTERVAL + random.randint(0, 20)),
        )
        return {}
