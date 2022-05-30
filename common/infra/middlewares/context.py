from django.http.request import HttpRequest

USER_KEY = 'uid'
TEN_YEARS = 60 * 60 * 24 * 365 * 10


class HttpRequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        request = HttpRequestContext(request)
        return request
