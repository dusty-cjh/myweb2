from django.urls import path

from . import views


app_name = 'wechat'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('retail/', views.RetailView.as_view(), name='retail'),
    path('retail/result/', views.RetailPayResultAPI.as_view(), name='api-retail-result'),

    path('mobile/', views.MobileView.as_view(), name='mobile'),
]
