from django.urls import path, include
from . import apis

app_name = 'mybot'
urlpatterns = [
    path('', apis.index, name='index'),
    path('test/event_loop/', apis.test_event_loop, name='test-event_loop'),
]
