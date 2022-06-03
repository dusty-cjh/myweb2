import re
from asgiref.sync import sync_to_async as s2a
from django.db.utils import OperationalError
from bridge.onebot import OneBotEvent, CQCode, AsyncOneBotApi, AbstractOneBotEventHandler, OneBotCmdMixin, Role
from mybot.models import OneBotEventTab


MSG_SUCCESS_KICK = '已踢'
MSG_ERR_INVALID_KICKED_USER_ID = '被踢人QQ号格式错误！'
MSG_ERR_BAD_PERMISSION = '无权操作！'
MSG_ERR_INTERNAL_SERVER_ERROR = '处理出错！请重试'

PLUGIN_NAME = '基本命令'


class OneBotEventHandler(AbstractOneBotEventHandler, OneBotCmdMixin):
    async def event_message_group(self, event: OneBotEvent, *args, **kwargs):
        # save message of groups matching patterns to DB

        pass

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

        return await super().event_message_private(event, *args, **kwargs)

    async def event_message_group_normal(self, event: OneBotEvent, *args, **kwargs):
        if Role.is_manager(event.sender['role']):
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
