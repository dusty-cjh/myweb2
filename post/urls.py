from django.urls import path

from . import views, apis

app_name = 'post'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    # path('shop/', views.ShopView.as_view(), name='shop'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('support/', views.SupportView.as_view(), name='support'),

    path('post/<int:pk>', views.PostDetailView.as_view(), name='post'),
    path('article/<int:pk>', views.ArticleDetailView.as_view(), name='article'),

    path('goto/', views.goto_test, name='goto'),

    path('MP_verify_cnuhJDCblRVDP7Vf.txt', views.wx_verify, name='wx-verify'),
]

urlpatterns += [
    path('cache/data/<str:name>', apis.get_cache_data, name='cache-data')
]
