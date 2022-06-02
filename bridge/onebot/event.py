from django.http.request import HttpRequest
from common.middlewares import LoggingContextAdapter
from common import utils
from .apis import AsyncOneBotApi as OneBotApi
from .serializers import OneBotEvent
from . import settings as constants

CLASS_NAME_PLUGIN_CONFIG = 'PluginConfig'


def create_event(event: dict) -> OneBotEvent:
    event = OneBotEvent(event)
    return event


def get_event_name(event: OneBotEvent):
    name = event.post_type
    if event.post_type in (constants.EVENT_POST_TYPE_MESSAGE, constants.EVENT_POST_TYPE_MESSAGE_SENT):
        name = '{}.{}'.format(name, event.message_type)
    elif event.post_type == constants.EVENT_POST_TYPE_REQUEST:
        name = '{}.{}'.format(name, event.request_type)
    elif event.post_type == constants.EVENT_POST_TYPE_NOTICE:
        name = '{}.{}'.format(name, event.notice_type)
    if hasattr(event, 'sub_type'):
        name = '{}.{}'.format(name, event.sub_type)
    return name


class AbstractOneBotEventHandler:
    log: LoggingContextAdapter

    def __init__(self, request: HttpRequest, context=None, **kwargs):
        self.context = context or dict()
        self.request = request
        self.log = getattr(request, 'log', None)
        self.api = OneBotApi()

    async def dispatch(self, event: OneBotEvent, *args, **kwargs):
        # validate permission
        if not await self.should_check(event, *args, **kwargs):
            return

        event_name = get_event_name(event)
        for handler_name in utils.chain(event_name.split('.'), sep='_', prefix='event'):
            if h := getattr(self, handler_name, None):
                return await h(event, *args, **kwargs)

    async def should_check(self, event: OneBotEvent, *args, **kwargs):
        return True

    async def is_group_message(self, event: OneBotEvent):
        return event.post_type == 'message' and event.message_type == 'group'

    # ============ message event ===============

    async def event_message_private_friend(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_private_group(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_private_group_self(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_private_other(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_group_normal(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_group_anonymous(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_message_group_notice(self, event: OneBotEvent, *args, **kwargs):
        pass

    # ============ self message event ===============

    async def event_message_sent_private_friend(self, event: OneBotEvent, *args, **kwargs):
        return await self.event_message_private_friend(event, *args, **kwargs)

    async def event_message_sent_private_group(self, event: OneBotEvent, *args, **kwargs):
        return await self.event_message_private_group(event, *args, **kwargs)
        pass

    async def event_message_sent_private_group_self(self, event: OneBotEvent, *args, **kwargs):
        return await self.event_message_private_group_self(event, *args, **kwargs)
        pass

    async def event_message_sent_private_other(self, event: OneBotEvent, *args, **kwargs):
        return await self.event_message_private_other(event, *args, **kwargs)
        pass

    async def event_message_sent_group_normal(self, event: OneBotEvent, *args, **kwargs):
        return await self.event_message_group_normal(event, *args, **kwargs)
        pass

    async def event_message_sent_group_anonymous(self, event: OneBotEvent, *args, **kwargs):
        return await self.event_message_group_anonymous(event, *args, **kwargs)
        pass

    async def event_message_sent_group_notice(self, event: OneBotEvent, *args, **kwargs):
        return await self.event_message_group_notice(event, *args, **kwargs)
        pass

    # ============= notice event ===============

    async def event_notice_group_upload(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_admin_set(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_admin_unset(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_decrease_leave(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_decrease_kick(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_decrease_kick_me(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_increase_approve(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_increase_invite(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_ban_ban(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_ban_lift_ban(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_friend_add(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_recall(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_friend_recall(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_notify_poke(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_notify_lucky_king(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_notify_honor(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_group_card(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_offline_file(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_client_status(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_essence_add(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_notice_essence_delete(self, event: OneBotEvent, *args, **kwargs):
        pass

    # ============= request event ===============

    async def event_request_friend(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_request_group_add(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def event_request_group_invite(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def meta_event(self, event: OneBotEvent, *args, **kwargs):
        pass


class OneBotCmdMixin:
    async def event_message_private_friend(self, event, *args, **kwargs):
        return await self.dispatch_cmd(event, *args, **kwargs)

    async def event_message_private_group(self, event: OneBotEvent, *args, **kwargs):
        return await self.dispatch_cmd(event, *args, **kwargs)

    async def event_message_group_normal(self, event: OneBotEvent, *args, **kwargs):
        return await self.dispatch_cmd(event, *args, **kwargs)

    async def dispatch_cmd(self, event: OneBotEvent, *args, **kwargs):
        cmd_args = event.message.strip().split()
        cmd_args.extend(args)

        if len(cmd_args) > 0:
            h = getattr(self, f'cmd_{cmd_args[0]}', None)
            if h:
                ret = await h(event, *cmd_args, **kwargs)
                return ret

    def _get_group_id(self, e: OneBotEvent, *args, **kwargs):
        gid = getattr(e, 'group_id', None)
        if not gid:
            return getattr(e, 'sender', {}).get('group_id')
        return gid
