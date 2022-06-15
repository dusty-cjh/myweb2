from django.http import HttpRequest, HttpResponse
from django.core.cache import cache


def get_cache_data(request: HttpRequest, name: str):
    data = cache.get(name)
    pass

