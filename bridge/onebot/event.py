import uuid
import ujson as json
from asgiref.sync import sync_to_async as s2a
from django.http.request import HttpRequest
from django.core.cache import cache
from common.middlewares import LoggingContextAdapter
from common.utils import serializer
from common import utils
from .apis import AsyncOneBotApi as OneBotApi
from .serializers import OneBotEvent
from . import settings as constants
from .models import AbstractPluginConfigs

CLASS_NAME_PLUGIN_CONFIG = 'PluginConfig'


def create_event(event: dict) -> OneBotEvent:
    event = OneBotEvent(event)
    event.raw_event = event
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


class AbstractOneBotPluginConfig(serializer.Serializer):
    name = serializer.CharField(default='')
    verbose_name = serializer.CharField(default='')
    short_description = serializer.CharField(default='')
    readonly_fields = 'name verbose_name'.split()
    plugin_config_model = AbstractPluginConfigs

    @classmethod
    def _get_module_name(cls):
        return cls.__module__.split('.')[-1]

    @classmethod
    def _serialize_default_config(cls):
        plugin_default_config = {}
        for field_name in cls._fields:
            field = getattr(cls, field_name)
            plugin_default_config[field_name] = field.default_value
        if not plugin_default_config['name']:
            plugin_default_config['name'] = cls._get_module_name()
        if not plugin_default_config['verbose_name']:
            plugin_default_config['verbose_name'] = plugin_default_config['name']
        return plugin_default_config

    @classmethod
    def get_default(cls):
        plugin_default_config = cls._serialize_default_config()
        return cls(**plugin_default_config)

    @classmethod
    def get_latest(cls):
        plugin_default_config = cls._serialize_default_config()
        try:
            obj = cls.plugin_config_model.objects.get(name=cls._get_module_name())
        except cls.plugin_config_model.DoesNotExist:
            # write default config to DB if it not exists
            kwargs = {}
            for field_name in cls.readonly_fields:
                kwargs[field_name] = plugin_default_config.pop(field_name)
            kwargs['configs'] = json.dumps(plugin_default_config)
            cls.plugin_config_model.objects.create(**kwargs)
            return cls.get_default()
        else:
            # read and then flush in DB plugin config
            plugin_db_config = json.loads(obj.configs)
            utils.update_json_obj(plugin_default_config, plugin_db_config)
            return cls(**plugin_default_config)

    @classmethod
    def from_db_config(cls, obj):
        plugin_configs = utils.update_json_obj(cls._serialize_default_config(), json.loads(obj.configs))
        return cls(**plugin_configs)

    @classmethod
    def json_form_fields(cls):
        return cls._fields ^ set(cls.readonly_fields)


class AbstractOneBotEventHandler:
    log: LoggingContextAdapter
    cfg_class = AbstractOneBotPluginConfig
    cfg: AbstractOneBotPluginConfig

    def __init__(self, request: HttpRequest, context=None, **kwargs):
        self.context = context or dict()
        self.request = request
        self.log = getattr(request, 'log', None)
        self.api = OneBotApi()

    async def get_cfg(self):
        # global
        cls = self.__class__
        _cfg_cache_key = getattr(cls, '_cfg_cache_key', uuid.uuid4().hex)

        key = await cache.aget(_cfg_cache_key)
        if not key:
            cls.cfg = await s2a(self.cfg_class.get_latest)()
            await cache.aset(_cfg_cache_key, 1, 60)
            setattr(cls, '_cfg_cache_key', _cfg_cache_key)

        return cls.cfg

    async def dispatch(self, event: OneBotEvent, *args, **kwargs):
        # load latest plugin config
        self.cfg = await self.get_cfg()

        # validate permission
        if not await self.should_check(event, *args, **kwargs):
            return

        # event_name = get_event_name(event)
        # for handler_name in utils.chain(event_name.split('.'), sep='_', prefix='event'):
        #     if h := getattr(self, handler_name, None):
        #         return await h(event, *args, **kwargs)
        event_name = 'event_' + event.post_type
        h = getattr(self, event_name, None)
        if h:
            return await h(event, *args, **kwargs)

    async def should_check(self, event: OneBotEvent, *args, **kwargs):
        return True

    async def is_group_message(self, event: OneBotEvent):
        return event.post_type == 'message' and event.message_type == 'group'

    # ============ message event ===============

    async def event_message(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_message_' + event.message_type, None)
        if h:
            return await h(event, *args, **kwargs)

    async def event_message_group(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_message_group_' + event.sub_type, None)
        if h:
            return await h(event, *args, **kwargs)

    async def event_message_private(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_message_private_' + event.sub_type, None)
        if h:
            return await h(event, *args, **kwargs)

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

    async def event_message_sent(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_message_sent_' + event.message_type, None)
        if h:
            return await h(event, *args, **kwargs)

    async def event_message_sent_private(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_message_sent_private_' + event.sub_type, None)
        if h:
            return await h(event, *args, **kwargs)

    async def event_message_sent_group(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_message_sent_group_' + event.sub_type, None)
        if h:
            return await h(event, *args, **kwargs)

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

    async def event_notice(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_notice_' + event.notice_type, None)
        if h:
            return await h(event, *args, **kwargs)

    async def event_notice_notify(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_notice_notify_' + event.sub_type, None)
        if h:
            return await h(event, *args, **kwargs)

    async def event_notice_essence(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_notice_essence_' + event.sub_type, None)
        if h:
            return await h(event, *args, **kwargs)

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

    async def event_request(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_request_' + event.request_type, None)
        if h:
            return await h(event, *args, **kwargs)

    async def event_request_group(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'event_request_group_' + event.sub_type, None)
        if h:
            return await h(event, *args, **kwargs)

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
