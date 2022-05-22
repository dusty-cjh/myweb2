import re
from mybot.models import AbstractOneBotEventHandler, OneBotCmdMixin, AbstractOneBotPluginConfig, serializer
from mybot.models import OneBotEvent
from mybot.onebot_apis import OneBotApi


MSG_SUCCESS_KICK = '已踢'
MSG_ERR_INVALID_KICKED_USER_ID = '被踢人QQ号格式错误！'
MSG_ERR_BAD_PERMISSION = '无权操作！'
MSG_ERR_INTERNAL_SERVER_ERROR = '处理出错！请重试'

PLUGIN_NAME = '基本命令'


class PluginConfig(AbstractOneBotPluginConfig):
    name = serializer.CharField(default='base_command')
    verbose_name = serializer.CharField(default='基础命令')
    cmd_prefix = serializer.CharField(default='/')


class OneBotEventHandler(AbstractOneBotEventHandler, OneBotCmdMixin):

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
        resp = await OneBotApi.get_group_member_info_with_cache(group_id, sender_id)
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
        resp = await OneBotApi.set_group_kick(
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
