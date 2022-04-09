import asyncio as aio
import time

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from common.kademlia import krpc
from common.constants import ErrCode, ErrMsg
from common.utils import error_response


# assign user custom krpc config
if hasattr(settings, 'KRPC_CONFIG'):
    krpc.DEFAULT_KRPC_CONFIG.update(getattr(settings, 'KRPC_CONFIG'))


def get_default() -> krpc.Krpc:
    ret = krpc.get_default()
    return ret


def with_default(coro):
    async def wrapper(*args, k: krpc.Krpc = None, **kwargs):
        if not k:
            k = get_default()
        start_time = time.time()
        resp = await coro(k=k, *args, **kwargs)
        resp['elapsed_time'] = int((time.time() - start_time)*1000)
        return resp
    return wrapper


def run(k: krpc.Krpc = None):
    if not k:
        k = get_default()

    ret = error_response(ErrCode.SUCCESS)
    try:
        k.start()
    except Exception as e:
        ret = error_response(ErrCode.SERVER_ERROR, 'start_default_krpc|exception=%s' % e)
    return ret


def stop(k: krpc.Krpc = None):
    if not k:
        k = get_default()

    ret = error_response(ErrCode.SUCCESS)
    try:
        k.stop()
    except Exception as e:
        ret = error_response(ErrCode.SERVER_ERROR, 'start_default_krpc|exception=%s' % e)
    return ret


def bootstrap_ping(k: krpc.Krpc = None):
    if not k:
        k = get_default()

    ret = error_response(ErrCode.SUCCESS)
    # try:
    #     k.core.bootstrap_by_ping()


@with_default
async def bootstrap(info_hash, timeout=10, k: krpc.Krpc =None, bootstrap_method=krpc.QueryType.FIND_NODE):
    if not k:
        k = get_default()

    l = aio.get_running_loop()
    aio.set_event_loop(k.loop)
    ret = dict()
    if bootstrap_method == krpc.QueryType.FIND_NODE:
        nodes = await k.core.bootstrap_by_find_node(krpc.dht_bootstrap_address)
    elif bootstrap_method == krpc.QueryType.GET_PEERS:
        nodes, peers = await k.core.bootstrap_by_get_peers(bytes.fromhex(info_hash), krpc.dht_bootstrap_address, timeout=timeout)
        ret['peers'] = peers
    else:
        nodes = await k.core.bootstrap_by_ping(krpc.dht_bootstrap_address)
        bootstrap_method = krpc.QueryType.PING

    ret['nodes'] = [x.information for x in nodes]
    aio.set_event_loop(l)
    return ret


@with_default
async def status(k: krpc.Krpc):
    ret = error_response(ErrCode.SUCCESS)
    addr = ('127.0.0.1', 6881)
    if not k.is_running():
        return error_response(ErrCode.KRPC_SERVER_NOT_START)

    try:
        resp = await k.core.ping(addr)
    except aio.TimeoutError:
        ret = error_response(ErrCode.TIMEOUT, 'timeout while self krpc ping')
        ret['ping'] = False
    else:
        ret['ping'] = resp.get_queried_id().hex()

    return ret
