from django.urls import path

from . import views
from . import apis


app_name = 'shop'
urlpatterns = [
	path('', views.IndexView.as_view(), name='index'),
	path('goods/<int:pk>/', views.GoodsDetailView.as_view(), name='goods'),
	path('order/<int:pk>/', views.OrderCreateView.as_view(), name='order-create'),
	path('order-create-callback', apis.OrderCreateCallbackAPI.as_view(), name='order-create-callback'),
	path('order-list/', views.OrderListView.as_view(), name='order-list'),
	path('order-detail/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
]