import asyncio as aio
import re
from asgiref.sync import async_to_sync as a2s
from django.core.cache import cache
from bridge.onebot import AsyncOneBotApi, AbstractOneBotEventHandler, CQCode
from bridge.onebot.permissions import message_from_manager
from mybot.event_loop import call
from .async_jobs import recall_message


class OneBotEventHandler(AbstractOneBotEventHandler):
    permission_list = [message_from_manager]
    ad_re_pattern = re.compile(
        r'^\s*(?:ad|alzheimer dementia|老年痴呆|alzheimer)\s*(stop|[1-9]\d*)\s*(min|sec|hours?|days?)?\s*$')

    async def event_message_group_normal(self, event, *args, **kwargs):
        # whether recall message, run in background
        call(self.process_message(event, *args, **kwargs))

        # get arguments
        m = self.ad_re_pattern.search(event.raw_message)
        if not m:
            return
        t, unit = m.groups()
        t = 0 if t == 'stop' else int(t)
        if unit:
            if unit.startswith('m'):
                t *= 60
            elif unit.startswith('h'):
                t *= 3600
            elif unit.startswith('d'):
                t *= 3600 * 24
        self.log.info('alzheimer dementia got args: {} for group {}', m.groups(), event.group_id)

        group_info, err = await self.api.with_max_retry(3).get_group_info(event.group_id)
        if err:
            self.log.warning('get group info failed, err={}, resp={}', err, group_info)

        # schedule periodic job
        # await recall_message.add_job(event.user_id, event.group_id, t)
        key = self.get_alzheimer_cache_key(event, *args, **kwargs)
        val = t
        await cache.aset(key, val)
        await self.api.send_private_msg(
            self.cfg.NOTI_RUNNING.format(
                group_id='{}({})'.format(group_info.get('group_name'), event.group_id),
                interval=t,
            ),
            event.user_id,
            event.group_id,
        )

    async def event_message_sent_group_normal(self, event, *args, **kwargs):
        return await self.event_message_group_normal(event, *args, **kwargs)

    async def process_message(self, event, *args, **kwargs):
        interval = await cache.aget(self.get_alzheimer_cache_key(event, *args, **kwargs))
        if interval:
            await aio.sleep(interval)
            resp, err = await self.api.delete_msg(event.message_id)
            if err:
                self.log.warning('recall message failed, err={}, resp={}', err, resp)

    def get_alzheimer_cache_key(self, event, *args, **kwargs):
        key = 'alzheimer_dementia_plugin.{}'.format(event.group_id)
        return key
