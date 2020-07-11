from django.urls import path

from . import views

app_name = 'post'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('shop/', views.ShopView.as_view(), name='shop'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('support/', views.SupportView.as_view(), name='support'),
]
