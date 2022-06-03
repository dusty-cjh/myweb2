from asgiref.sync import async_to_sync as a2s
from bridge.onebot import AsyncOneBotApi, OneBotApi, AbstractOneBotEventHandler, OneBotCmdMixin, create_event


class OneBotEventHandler(AbstractOneBotEventHandler, OneBotCmdMixin):
    pass

