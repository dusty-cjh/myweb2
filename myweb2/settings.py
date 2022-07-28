"""
Django settings for myweb2 project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from django.utils.translation import gettext_lazy as _
import pytz

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/
ENV = os.environ.get('env', 'test')
DEBUG = False if ENV == 'live' else True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'w9f5sp*d1d_4%183(3^q1vi@!ne)&#00+6nc7+tc)7r$jzq-c+'

ALLOWED_HOSTS = ['*']

USE_X_FORWARDED_HOST = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'wechat.apps.WechatConfig',
    'post.apps.PostConfig',
    'config.apps.ConfigConfig',
    'collect.apps.CollectConfig',
    # 'resource2.apps.ResourceConfig',
    'shop.apps.ShopConfig',
    'mybot.apps.MybotConfig',

    'rest_framework',
    'ckeditor',
    'ckeditor_uploader',
    'django_ckeditor_5',
    'django_filters',
    # 'django_celery_results',
    # 'django_celery_beat',
    'django_prometheus',
    'widget_tweaks',
]
SITE_ID = 2 if ENV == 'live' else 1

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.middlewares.AccessLogMiddleware',
    'post.middleware.UserIDMiddleware',
    'config.middlewares.CorsMiddleWare',    # CORS
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'myweb2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'plugins', '*', 'templates'), ]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # `allauth` needs this from django
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'myweb2.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/
LANGUAGES = [
    ('zh-hans', _('Chinese')),
    ('en', _('English')),
]
LANGUAGE_CODE = 'zh-hans'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

TIME_ZONE = 'Asia/Shanghai'
PY_TIME_ZONE = pytz.timezone(TIME_ZONE)

USE_I18N = True

USE_L10N = True

USE_TZ = True

# AUTH_USER_MODEL = 'user.MyUser' # 在源码中修改

DOMAIN = 'hdcjh.xyz'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'live': {
        # 'hdcjh': {    # deploy in hdcjh.xyz
        #     'ENGINE': 'django.db.backends.mysql',
        #     'NAME': 'myweb2',
        #     'USER': 'cjh',
        #     'PASSWORD': '123456',
        #     'HOST': '127.0.0.1',
        #     'PORT': '3306',
        #     'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        # },
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'myweb2_live',
            'USER': 'myweb2_live',
            'PASSWORD': 'p7jKfeSwpHEGrDT2',
            'HOST': '127.0.0.1',
            'PORT': '3306',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'onebot': {
            # 'ENGINE': 'django.db.backends.sqlite3',
            'ENGINE': 'django_prometheus.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'onebot.sqlite3'),
        },
    },
    'test': {
        'sqlite3': {
            # 'ENGINE': 'django.db.backends.sqlite3',
            'ENGINE': 'django_prometheus.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        },
        'hdcjh': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'myweb2_test',
            'USER': 'myweb2_test',
            'PASSWORD': 'vjq9g8349ghnb30f32e9z',
            'HOST': 'hdcjh.xyz',
            'PORT': '3306',
            'init_command': "SET foreign_key_checks = 0;",
        },
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'myweb2_test',
            'USER': 'myweb2_test',
            'PASSWORD': 's2ffKte5ZT7X4TZj',
            'HOST': 'crash.hdcjh.xyz',
            'PORT': '3306',
            'init_command': "SET foreign_key_checks = 0;",
        },
        'onebot': {
            # 'ENGINE': 'django.db.backends.sqlite3',
            'ENGINE': 'django_prometheus.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'onebot.sqlite3'),
        },
    },
}
DATABASES = DATABASES[ENV]

DATABASE_ROUTERS = ['mybot.models.OneBotEventDBRouter', ]

CACHES = {
    'test': {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        },
    },
    'live': {
        'default': {
            'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
            # 'BACKEND': 'django_redis.cache.RedisCache',
            "LOCATION": "redis://127.0.0.1:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "MAX_ENTRIES": 30000,
            },
        },
    },
}
CACHES = CACHES[ENV]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ckeditor
CKEDITOR_UPLOAD_PATH = 'ckimage/'

## simple ui
# SIMPLEUI_DEFAULT_THEME = 'admin.lte.css'

# rest framework
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 8,
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend', ),   # filter backend
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = {
    'test': os.path.join(BASE_DIR, 'static'),
    'live': os.path.join(BASE_DIR, 'static'),
}
STATIC_ROOT = STATIC_ROOT[ENV]

MEDIA_URL = '/media/'
MEDIA_ROOT = {
    'test': os.path.join(BASE_DIR, 'media'),
    'live': os.path.join(BASE_DIR, 'media'),
}
MEDIA_ROOT = MEDIA_ROOT[ENV]

RESOURCE_URL = os.path.join(STATIC_URL, 'resource')
RESOURCE_ROOT = os.path.join(STATIC_ROOT, 'resource')

ADMINS = [('Jiaohao.chen', 'jiahao.chen@seamoney.com'), ('dusty-cjh', 'dusty-cjh@qq.com'), ]

# mail alert config
EMAIL_CONFIG = {
    'sina': {
        'host': 'smtp.sina.cn',
        'port': 587 if ENV == 'live' else 25,
        'user': 'hdcjh_xyz@sina.cn',
        'password': '04a167768fbad283',
        'use_tls': False
    },
    'qq': {
        'host': 'smtp.qq.com',
        'port': 587 if ENV == 'live' else 25,
        'user': 'dusty-cjh@qq.com',
        'password': 'aparzwxdjqgedhcc',
        'use_tls': True
    },
}
EMAIL_CONFIG = EMAIL_CONFIG['sina']

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = EMAIL_CONFIG['host']
EMAIL_PORT = EMAIL_CONFIG['port']
EMAIL_HOST_USER = EMAIL_CONFIG['user']
EMAIL_HOST_PASSWORD = EMAIL_CONFIG['password']
EMAIL_USE_TLS = EMAIL_CONFIG['use_tls']
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# 微信号 小蛮三
WECHAT = {
    'app_id': 'wx23279c94c52ac9fd',
    'app_secret': '8f783a4be8d36801e201ab170bcacc56',
    'token': 'StSVhLSKDMO3JieDpLKlZjd0VTtT0lKa',
    'aes_key': 'PSPvTKY8KbvHMnTlUBNdwOw5YYjID6CUPHbiIhfqH5b==',
    'merchant_id': '1609790020',
    'merchant_api_key': '01234567890123456789012345678901',
    'merchant_key': os.path.join(STATIC_ROOT, 'cert', 'apiclient_key.pem'),
    'merchant_cert': os.path.join(STATIC_ROOT, 'cert', 'apiclient_cert.pem'),
    'is_crypto': True,
}

ASYNC_JOB = {
    'MAX_LIFETIME': 600 if DEBUG else 3600 * 2,
    'MAX_RETRY': 3,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname}|{asctime}|{module}|{message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname}|{message}',
            'style': '{',
        },
        'info': {
            'format': '{levelname}|{asctime}|{message}',
            'style': '{',
        },
        'heavy': {
            'format': '{levelname}|{asctime}|{pathname}:{lineno}|{message}',
            'style': '{',
        },
        'error': {
            'format': '{asctime}|{pathname}:{lineno}|{message}',
            'style': '{',
        },
        'access': {
            'format': '{levelname}|{asctime}|{message}',
            'style': '{',
        },
        'data': {
            'format': '{asctime}|{message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'daemon': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'daemon.log'),
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
        'info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'info.log'),
            'formatter': 'info',
            'encoding': 'utf8'
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'error.log'),
            'formatter': 'error',
            'encoding': 'utf8'
        },
        'access': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'access.log'),
            'formatter': 'access',
            'encoding': 'utf8'
        },
        'data': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'data.log'),
            'formatter': 'data',
            'encoding': 'utf8'
        },
        'async_job': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'log', 'async_job.log'),
            'formatter': 'data',
            'encoding': 'utf8'
        },
    },
    'root': {
        'handlers': ['console', 'daemon', ] if DEBUG else ['daemon', ],
        'level': 'INFO',
    },
    'loggers': {
        'info': {
            'handlers': ['info', 'mail_admins', ],
            'level': 'INFO',
            'formatter': 'info',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['access', ],
            'level': 'INFO',
            'formatter': 'verbose',
        },
        'access': {
            'handlers': ['access', ],
            'level': 'INFO',
            'formatter': 'access',
            'propagate': False,
        },
        'error': {
            'handlers': ['error', ],
            'propagate': False,
        },
        # to collect user statistics
        'data': {
            'handlers': ['data', ],
            'propagate': False,
        },
        'async_job': {
            'handlers': ['async_job', ],
            'propagate': False,
        },
    },
}

# rabbit mq
RABBIT_MQ = {
    'test': {
        'url': 'amqp://localhost:5672/',
        'exchange': [
            {
                'name': 'onebot.message.private',
                'type': 'direct',
            },
            {
                'name': 'onebot.message.group',
                'type': 'direct',
            },
        ],
    },
    'live': {
        'url': 'amqp://localhost:5672/',
        'exchange': [
            {
                'name': 'onebot.message.private',
                'type': 'direct',
            },
            {
                'name': 'onebot.message.group',
                'type': 'direct',
            },
        ],
    },
}
RABBIT_MQ = RABBIT_MQ[ENV]

# Celery Configuration Options
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 3600
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'

# all auth
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

INSTALLED_APPS += [

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # # ... include the providers you want to enable:
    # 'allauth.socialaccount.providers.apple',
    # 'allauth.socialaccount.providers.baidu',
    # 'allauth.socialaccount.providers.facebook',
    # 'allauth.socialaccount.providers.figma',
    'allauth.socialaccount.providers.github',
    # 'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.twitter',
    # 'allauth.socialaccount.providers.weibo',
    # 'allauth.socialaccount.providers.weixin',
    # 'allauth.socialaccount.providers.feishu',
]

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': '4831c48c92f9e6db4b59',
            'secret': 'e31c8a4c33b4df3298cd9b4b0a630ac64b48e556',
            'key': ''
        },
        "VERIFIED_EMAIL": True,
    }
}

LOGIN_REDIRECT_URL = '/'
