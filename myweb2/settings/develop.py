from .base import *  # NOQA


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# # Database
# # https://docs.djangoproject.com/en/3.0/ref/settings/#databases
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'myweb2',
        'USER': 'cjh',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    }
}


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# STATIC_ROOT = '/opt/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# MEDIA_ROOT = '/opt/media/'


# 静态资源 resource
RESOURCE_URL  = os.path.join(STATIC_URL, 'resource')
RESOURCE_ROOT = os.path.join(STATIC_ROOT, 'resource')


# 微信号 小蛮三
WECHAT = {
    'app_id': 'wx23279c94c52ac9fd',
    'app_secret': '418cac276c34ece925da28a9ebd8f52b',
    'token': 'StSVhLSKDMO3JieDpLKlZjd0VTtT0lKa',
    'aes_key': 'M88JHVgq1VuNN8CGmvNUgbnHfGhgVHH8gYBhJ6FhcgH',
    'merchant_id': '1609790020',
    'merchant_api_key': '01234567890123456789012345678901',
    'merchant_key': os.path.join(STATIC_ROOT, 'cert', 'apiclient_key.pem'),
    'merchant_cert': os.path.join(STATIC_ROOT, 'cert', 'apiclient_cert.pem'),
}

