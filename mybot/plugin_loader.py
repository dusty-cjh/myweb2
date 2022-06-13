import os
import sys
import cachetools
import ujson
import importlib
from asgiref.sync import sync_to_async as s2a
from rest_framework.serializers import Serializer
from django.http.request import HttpRequest
from django.conf import settings
from bridge.onebot import create_event, AbstractOneBotEventHandler
from .models import AbstractOneBotPluginConfig, OneBotEventTab
from . import event_loop


class _module_hint:
    OneBotEventHandler: AbstractOneBotEventHandler
    PluginConfig: AbstractOneBotPluginConfig


PLUGIN_MODULES = dict()


def get_plugin(name: str) -> _module_hint:
    return PLUGIN_MODULES.get(name)


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
    plugin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
    plugin_list = [x for x in os.listdir(plugin_dir) if not x.startswith('_')]

    # import file plugin
    plugins = [x[:-3] for x in plugin_list if x.endswith('.py')]
    plugins.extend([x for x in plugin_list if os.path.isdir(os.path.join(plugin_dir, x))])
    for p in plugins:
        # import modules
        plugin_module_name = 'mybot.plugins.%s' % p
        plugin_module = importlib.import_module(plugin_module_name)

        # validate
        h = getattr(plugin_module, 'OneBotEventHandler', None)
        if not h:
            raise ImportError('plugin %s has no OneBotEventHandler class' % plugin_module_name)
        if not issubclass(h, AbstractOneBotEventHandler):
            raise ImportError(
                'handler %s.OneBotEventHandler must be subclass of AbstractOneBotEventHandler' % plugin_module_name)
        cfg_class = getattr(plugin_module, 'PluginConfig', None)
        if not cfg_class:
            raise ImportError('plugin %s has no PluginConfig class' % plugin_module_name)
        if not issubclass(cfg_class, AbstractOneBotPluginConfig):
            raise ImportError(
                'handler %s.PluginConfig must be subclass of AbstractOneBotPluginConfig' % plugin_module_name)
        # cfg = cfg_class.get_latest()
        cfg = cfg_class()
        if cfg.name is None:
            raise ValueError('%s.PluginConfig.name not be assigned' % plugin_module_name)
        if cfg.verbose_name is None:
            cfg.verbose_name = cfg.name.replace('_', ' ').replace('-', ' ')

        # auto-inject plugin class to handler
        h.cfg_class = cfg_class

        # register plugin
        PLUGIN_MODULES[p] = plugin_module

        if settings.DEBUG:
            print('[plugin_loader]\t', '\t - '.join([cfg.name, cfg.verbose_name, cfg.short_description]), file=sys.stderr)


import_plugins()


@cachetools.cached(cache=cachetools.TTLCache(maxsize=10, ttl=60))
def get_sorted_event_handlers():
    handlers = sorted(
        map(lambda module: module.OneBotEventHandler, PLUGIN_MODULES.values()),
        key=lambda h: h.get_cfg_sync().sort_weight,
        reverse=True,
    )
    return list(handlers)


async def dispatch(request: HttpRequest):
    event_loop.get_event_loop()
    raw_event = ujson.loads(request.body)
    event = create_event(raw_event)

    # handle by task
    if resp := event_loop.process_message(request, event) is not None:
        return resp

    # handle by event
    handler_list = await s2a(get_sorted_event_handlers)()
    for handle_class in handler_list:
        h = handle_class(request)
        resp = await h.dispatch(event)
        if isinstance(resp, Serializer):
            return resp.data
        elif isinstance(resp, dict):
            return resp
