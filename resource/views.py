import logging
from django.http import HttpResponse, JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from manager import wechat_manager


log = logging.getLogger('info')


def cors_headers(func):
    def decorator(*args, **kwargs):
        resp = func(*args, **kwargs)
        # for key, val in {
        #     'Access-Control-Allow-Origin': '*',
        #     'Allow': 'POST,OPTIONS',
        #     'Access-Control-Allow-Methods': 'POST,OPTIONS',
        # }.items():
        #     resp.setdefault(key, val)
        return resp
    return decorator


class UploadImageView(View):
    @csrf_exempt
    @cors_headers
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request: HttpRequest):
        files = list(request.FILES.values())
        if len(files) == 0:
            log.warning('upload-image does not receive any image data')
            return JsonResponse({
                'errcode': HttpResponseBadRequest.status_code,
                'errmsg': b'upload-image does not receive any image data',
            }, status=HttpResponseBadRequest.status_code)

        resp = wechat_manager.upload_image(files[0])

        return JsonResponse(data=resp)

