import time
import asyncio as aio
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from common.constants import ErrCode, ErrMsg
from common.utils import error_response
from common.kademlia import bittorrent as bt
from common.kademlia.node import Node


# assign user custom krpc config
if hasattr(settings, 'BIT_TORRENT_CONFIG'):
    bt.DEFAULT_BIT_TORRENT_CONFIG.update(getattr(settings, 'BIT_TORRENT_CONFIG'))


def get_default() -> bt.BitTorrent:
    ret = bt.get_default()
    return ret


def with_default(coro):
    async def wrapper(*args, obj: bt.BitTorrent = None, **kwargs):
        if not obj:
            obj = get_default()
        start_time = time.time()
        resp = await coro(obj=obj, *args, **kwargs)
        resp['elapsed_time'] = int((time.time() - start_time)*1000)
        return resp
    return wrapper


def run(b: bt.BitTorrent = None):
    if not b:
        b = get_default()

    ret = error_response(ErrCode.SUCCESS)
    try:
        b.start()
    except Exception as e:
        ret = error_response(ErrCode.SERVER_ERROR, 'start_default_krpc|exception=%s' % e)
    return ret


def stop(obj: bt.BitTorrent = None):
    if not obj:
        obj = get_default()

    ret = error_response(ErrCode.SUCCESS)
    try:
        obj.stop()
    except Exception as e:
        ret = error_response(ErrCode.SERVER_ERROR, 'start_default_krpc|exception=%s' % e)
    return ret


@with_default
async def status(obj: bt.BitTorrent):
    if not obj.is_running():
        run()
        await aio.sleep(1)

    await bt.handshake_with_remote(obj.peer_id.data)
    # # create bit torrent client
    # ret = error_response(ErrCode.SUCCESS)
    # client = bt.BitTorrent(
    #     is_client=True,
    #     address=('127.0.0.1', 6882),
    #     info_hash=Node.create_random().data,
    #     peer_id=obj.peer_id,
    # )
    # client.start()
    # await aio.sleep(2)  # wait until finishing handshake
    # print('get status')
    # ret['status'] = bt.BitTorrentProtocol.STATUS[client.core.status]
    # print('stop bt client')
    #
    # client.stop()
    # print('stoped')

    return error_response(ErrCode.SUCCESS)
