from django.urls import path, include
from . import apis

app_name = 'mybot'
urlpatterns = [
    path('', apis.index, name='index'),
    path('test/', apis.test_async, name='test'),
]
