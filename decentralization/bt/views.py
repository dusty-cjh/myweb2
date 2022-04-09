from django.http import HttpRequest, HttpResponse, JsonResponse, Http404, HttpResponseForbidden
from . import manager


def run(request: HttpRequest):
    ret = manager.run()
    return JsonResponse(ret)


def stop(request: HttpRequest):
    ret = manager.stop()
    return JsonResponse(ret)


async def bootstrap(request: HttpRequest):
    # parse arguments
    method = request.GET.get('method', 'ping')
    info_hash = request.GET.get('info_hash', '9107D4206AD3F4447B01920760565EC03F769174')
    timeout = request.GET.get('timeout', 10)

    # get result
    ret = await manager.bootstrap(info_hash, timeout, bootstrap_method=method)

    return JsonResponse(ret)


async def status(request: HttpRequest):
    resp = await manager.status()
    return JsonResponse(resp)

