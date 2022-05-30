import time
import pika
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async as s2a
import asyncio as aio
from bridge.onebot import AsyncOneBotApi
from common.infra.rabbitmq import init
from common import utils
import queue
from pika.adapters.asyncio_connection import AsyncioConnection
from .event_loop import get_event_loop
from .models import OneBotEventTab


class OneBotPrivateMessageSession:
    def __init__(self, user_id, group_id=None, start_time=None, options=None):
        if start_time is None:
            start_time = utils.get_datetime_now()

        self.user_id = user_id
        self.group_id = group_id
        self.cursor_time = start_time
        self.message_pool = queue.Queue(maxsize=2000)
        self.api = AsyncOneBotApi(options)

    async def get_message(self, timeout=600):
        if not self.message_pool.empty():
            return self.message_pool.get_nowait()

        timeout_stamp = utils.get_datetime_now() + timedelta(seconds=timeout)
        while (cur := utils.get_datetime_now()) < timeout_stamp:
            # fresh data from DB
            queryset = OneBotEventTab.objects.filter(user_id=self.user_id, time__gt=self.cursor_time)
            if self.group_id is not None:
                queryset = queryset.filter(group_id=self.group_id)

            # sleep for a while if DB got no data
            size = await s2a(lambda: len(queryset))()
            if size == 0:
                await aio.sleep(5)

            # put messages into queryset
            else:
                self.cursor_time = cur
                for item in queryset[1:]:
                    self.message_pool.put(item)
                return queryset[0]
