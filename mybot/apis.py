import asyncio as aio
import ujson
from functools import wraps
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse
from common import get_logger
from common.decorators import async_csrf_exempt, async_access_log
from . import plugin_loader


@async_csrf_exempt
@async_access_log('mybot')
async def index(request: HttpRequest, *args, **kwargs):
    # plugin handle
    resp = await plugin_loader.dispatch(request)
    if resp:
        try:
            return JsonResponse(resp)
        except Exception as e:
            request.log.error('mybot.apis.index|response=%s|exception=%s' % (resp, repr(e)))
            return HttpResponse(b'', status=200)
    else:
        return HttpResponse(b'', status=200)
