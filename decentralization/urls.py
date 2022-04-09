from django.urls import path, include

from . import views

app_name = 'decentralization'
urlpatterns = [
    path('krpc/', include('decentralization.krpc.urls')),
    path('bt/', include('decentralization.bt.urls')),
]
