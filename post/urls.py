from django.urls import path

from . import views

app_name = 'post'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    # path('shop/', views.ShopView.as_view(), name='shop'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('support/', views.SupportView.as_view(), name='support'),

    path('post/<int:pk>', views.PostDetailView.as_view(), name='post'),

    path('MP_verify_cnuhJDCblRVDP7Vf.txt', views.wx_verify, name='wx-verify'),
]
