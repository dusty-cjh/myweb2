import logging
from django.http import HttpResponse, JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from manager import wechat_manager

from manager import utils


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

    def has_permission(self):
        key = settings.WECHAT['aes_key']
        if key in self.request.FILES:
            return True

        if self.request.user.is_staff:
            return True

    def post(self, request: HttpRequest):
        if not self.has_permission():
            return utils.json_error_response('have no permission')

        files = list(request.FILES.values())
        if len(files) == 0:
            log.warning('upload-image does not receive any image data')
            return utils.json_error_response('upload-image does not receive any image data')

        resp = wechat_manager.upload_image(files[0])
        request.log.info('resource.UploadImageView.post|response={}'.format(resp))
        return utils.json_response(data=resp, status=201)
