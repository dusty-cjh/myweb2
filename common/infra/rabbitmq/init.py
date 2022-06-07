import os
import ujson as json
import time
import pika
import threading
from django.conf import settings
from pika.adapters.asyncio_connection import AsyncioConnection


LOCAL = threading.local()
_REQUEST_CHANNEL_KEY = '_rmq_ch'


def create_connection():
    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBIT_MQ['url']))
    init_exchange(connection.channel())
    print('connected with %s, elapsed time:' % settings.RABBIT_MQ['url'], '\trabbitMQ status:', connection.is_open)
    return connection


def get_channel():
    """thread safe channel getter"""
    conn = getattr(LOCAL, 'CONN', None)
    if not conn or not conn.is_open:
        conn = create_connection()
        setattr(LOCAL, 'CONN', conn)
    return conn.channel()


def init_exchange(ch):
    for ex in settings.RABBIT_MQ['exchange']:
        ch.exchange_declare(
            ex['name'],
            exchange_type=ex['type'],
            durable=True,
        )


def set_channel_for_request(request):
    ch = get_channel()
    setattr(request, _REQUEST_CHANNEL_KEY, ch)
    return ch


def get_or_create_channel_on_request(request):
    ret = getattr(request, _REQUEST_CHANNEL_KEY, None)
    if ret is None:
        ret = set_channel_for_request(request)
    return ret
