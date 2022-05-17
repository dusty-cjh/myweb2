import os
import sys
import ujson
import importlib
from typing import Optional, List, Dict, Mapping, Iterable, ByteString

from rest_framework.serializers import Serializer
from django.http.request import HttpRequest

from .models import AsyncJobLock, AsyncJob, OneBotEvent, create_event, AbstractOneBotEventHandler
from . import event_loop

EVENT_HANDLERS = dict()


def register_event_handler(plugin):
    # import all modules
    module = importlib.import_module('mybot.plugins.%s' % plugin)

    # get specified class
    h = getattr(module, 'OneBotEventHandler', None)
    if not h:
        return None, 'module has no OneBotEventHandler class'

    # get plugin name
    plugin_name = getattr(module, 'PLUGIN_NAME', None)
    if not plugin_name or not isinstance(plugin_name, str):
        return None, 'module has no PLUGIN_NAME'

    # validate
    if not issubclass(h, AbstractOneBotEventHandler):
        return None, 'handler must be subclass of AbstractOneBotEventHandler'

    # add plugin
    setattr(h, 'plugin_name', plugin_name)
    return h, None


def import_plugins():
    success = []
    failed = []
    plugin_list = os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins'))

    # import file plugin
    plugins = [x[:-3] for x in plugin_list if x.endswith('.py') and x != '__init__.py']
    for p in plugins:
        h, errmsg = register_event_handler(p)
        if errmsg:
            failed.append((p, errmsg))
        else:
            EVENT_HANDLERS[p] = h
            success.append((p, getattr(h, 'plugin_name', '')))

    for row in success:
        print('[plugin_loader.success]\t', '\t - '.join(row), file=sys.stderr)
    for row in failed:
        print('[plugin_loader.failed]\t', '\t - '.join(row), file=sys.stderr)


import_plugins()


async def dispatch(request: HttpRequest):
    event_loop.get_event_loop()
    event = create_event(ujson.loads(request.body))

    # handle by task
    if resp := event_loop.process_message(request, event) is not None:
        return resp

    # handle by event
    for plugin_name, h_cls in EVENT_HANDLERS.items():
        h = h_cls(request=request)
        resp = await h.dispatch(event)
        if isinstance(resp, Serializer):
            return resp.data
        elif isinstance(resp, dict):
            return resp
