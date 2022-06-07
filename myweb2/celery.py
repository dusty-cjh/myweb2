import os
from django.conf import settings
from celery import Celery

"""
refer: https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

django celery results
    1. refer: https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html
    2. celery -A myweb2 worker -l INFO
django celery beat 
 1. celery -A myweb2 beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
 2. refer: https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#beat-custom-schedulers
 
"""

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myweb2.settings')

app = Celery('myweb2',
             broker=settings.RABBIT_MQ['url'],
             )

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
