"""
WSGI config for myweb2 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

profile = os.environ.get('ENV', 'test')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb2.settings.{}'.format(profile))

application = get_wsgi_application()
