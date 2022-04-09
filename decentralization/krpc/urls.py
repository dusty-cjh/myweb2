from django.urls import path

from . import views

app_name = 'krpc'
urlpatterns = [
    path('run/', views.run, name='run'),
    path('stop/', views.stop, name='stop'),
    path('bootstrap/', views.bootstrap, name='bootstrap'),
    path('status/', views.status, name='status'),
]
