import json
import os
import sys
import ujson
import importlib
import inspect
from functools import wraps
from typing import Optional, List, Dict, Mapping, Iterable, ByteString

from rest_framework.serializers import Serializer
from django.http.request import HttpRequest
from common import utils
from .models import OneBotEvent, create_event, AbstractOneBotEventHandler, AbstractOneBotPluginConfig, PluginConfigs
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
    plugin_list = os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins'))

    # import file plugin
    plugins = [x[:-3] for x in plugin_list if x.endswith('.py') and not x.startswith('_')]
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
        cfg = getattr(plugin_module, 'PluginConfig', None)
        if not cfg:
            raise ImportError('plugin %s has no PluginConfig class' % plugin_module_name)
        if not issubclass(cfg, AbstractOneBotPluginConfig):
            raise ImportError(
                'handler %s.PluginConfig must be subclass of AbstractOneBotPluginConfig' % plugin_module_name)
        cfg = cfg.get_latest()
        if cfg.name is None:
            raise ValueError('%s.PluginConfig.name not be assigned' % plugin_module_name)
        if cfg.verbose_name is None:
            cfg.verbose_name = cfg.name.replace('_', ' ').replace('-', ' ')

        # register plugin
        PLUGIN_MODULES[cfg.name] = plugin_module

        # # makesure plugin config has exist
        # config_items = {}
        # for k in dir(plugin_module.PluginConfig):
        #     if not k.startswith('_'):
        #         v = getattr(plugin_module.PluginConfig, k, None)
        #         config_items[k] = v
        # kwargs = dict(
        #     name=config_items.pop('name'),
        #     verbose_name=config_items.pop('verbose_name'),
        # )
        # try:
        #     plugin_config = PluginConfigs.objects.get(name=plugin_module.PluginConfig.name)
        # except PluginConfigs.DoesNotExist:
        #     kwargs['configs'] = json.dumps(config_items) or '{}',
        #     PluginConfigs.objects.create(**kwargs)
        # else:
        #     config_items.update(json.loads(plugin_config.configs))
        #     configs = json.dumps(config_items)
        #     if configs != plugin_config.configs:
        #         plugin_config.configs = configs
        #         plugin_config.save()

        print('[plugin_loader]\t', '\t - '.join([cfg.name, cfg.verbose_name, cfg.short_description]), file=sys.stderr)


import_plugins()


async def dispatch(request: HttpRequest):
    event_loop.get_event_loop()
    event = create_event(ujson.loads(request.body))

    # handle by task
    if resp := event_loop.process_message(request, event) is not None:
        return resp

    # handle by event
    for plugin_name, module in PLUGIN_MODULES.items():
        h = module.OneBotEventHandler(request=request)
        resp = await h.dispatch(event)
        if isinstance(resp, Serializer):
            return resp.data
        elif isinstance(resp, dict):
            return resp
