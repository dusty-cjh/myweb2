from django.urls import path

from . import views

app_name = 'bt'
urlpatterns = [
    path('run/', views.run, name='run'),
    path('stop/', views.stop, name='stop'),
    path('status/', views.status, name='status'),
]
