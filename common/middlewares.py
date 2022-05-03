import logging, uuid
from typing import Any, MutableMapping, Tuple
from django.http.request import HttpRequest

from django.http.request import HttpRequest


HEADER_HTTP_REQUEST_ID = 'X-Request-ID'


class LoggingContextAdapter:
    _access = logging.getLogger('access')
    _info = logging.getLogger('info')
    _error = logging.getLogger('error')
    _data = logging.getLogger('data')

    def __init__(self, *args, **kwargs):
        self._args = [str(x) for x in args]
        self._fields = kwargs

    def render_fields(self, msg):
        return '|'.join(self._args) + '|'+msg+'|'+'|'.join(['{}={}'.format(k, v) for k, v in self._fields.items()])

    def info(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self._info.info(self.render_fields(data))

    def warning(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self._info.warning(self.render_fields(data))

    def error(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self._error.error(self.render_fields(data))

    def access(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self._access.info(self.render_fields(data))

    def data(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self._data.info(self.render_fields(data))

    def with_field(self, key, val):
        obj = self.__class__(*self._args, **self._fields.copy())
        obj._fields[key] = val
        return obj

    def with_fields(self, fields):
        obj = self.__class__(*self._args, **self._fields.copy())
        obj._fields.update(**fields)
        return obj


class AccessLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        # get request id
        global log
        id = self.get_request_id(request)
        logger = LoggingContextAdapter(id)

        # parse user id
        if request.user.is_authenticated:
            logger = logger.with_fields({
                'url': request.get_full_path(),
                'userid': request.user.id,
                'session': request.session.session_key,
                'method': request.method,
            })

        # apply log to request as a property
        setattr(request, 'log', logger)

        # get response
        resp = self.get_response(request)

        return resp

    def get_request_id(self, request: HttpRequest):
        id = request.headers.get(HEADER_HTTP_REQUEST_ID, None)
        if id is None:
            id = uuid.uuid4().hex
        return str(id)


def get_logger(request: HttpRequest) -> LoggingContextAdapter:
    logger = getattr(request, 'log')
    if not logger:
        raise AttributeError('common.get_logger|req obj has no log attr, check whether added AccessLogMiddleware')
    return logger
