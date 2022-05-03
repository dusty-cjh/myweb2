from django.http.request import HttpRequest
from common.middlewares import LoggingContextAdapter
from .models import AsyncJob, OneBotEvent


class BasePlugin:
    log: LoggingContextAdapter
    plugin_name: str

    def __init__(self, *args, request: HttpRequest = None, context=None, **kwargs):
        if context is None:
            context = dict()

        self.context = context
        self.request = request
        self.log = request.log

    @classmethod
    def setup(cls, handlers: dict):
        handlers[cls.plugin_name] = cls

    async def dispatch(self, event: OneBotEvent):
        pass


class BaseRequestHandler(BasePlugin):
    async def dispatch(self, event: OneBotEvent, *args, **kwargs):
        if event.request_type == 'friend':
            return await self.friend(event, *args, **kwargs)
        elif event.sub_type == 'add':
            return await self.add(event, *args, **kwargs)
        else:
            return await self.invite(event, *args, **kwargs)

    async def friend(self,
                     event: OneBotEvent,
                     *args, **kwargs) -> OneBotEvent:
        pass

    async def add(self, event: OneBotEvent, *args, **kwargs) -> OneBotEvent:
        pass

    async def invite(self, event: OneBotEvent, *args, **kwargs) -> OneBotEvent:
        pass


class BaseMessageHandler(BasePlugin):
    async def message(self, event: OneBotEvent, *args, **kwargs):
        h = getattr(self, 'message_%s' % event.sub_type, None)
        if h:
            return h(event, *args, **kwargs)

    async def message_friend(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def message_group(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def message_group_self(self, event: OneBotEvent, *args, **kwargs):
        pass

    async def message_other(self, event: OneBotEvent, *args, **kwargs):
        pass


class BaseAsyncJobHandler:
    job_name = 'default_job'
    handler_name = 'BaseAsyncJobHandler'
    exec_interval = 30

    def __call__(self, params: dict, job: AsyncJob):
        pass
