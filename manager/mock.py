from functools import wraps
from django.conf import settings


def return_fixed_data(data=None, mock_in_live=False):
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if mock_in_live and settings.ENV == 'live':
                return func(*args, **kwargs)
            return data
        return inner
    return decorator
