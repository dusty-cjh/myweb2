import pika

from .init import create_connection

conn, ch = create_connection()

ch.exchange_declare(
    exchange='onebot',
    exchange_type='fanout',
)

ch.queue_declare(queue='', exclusive=True)

