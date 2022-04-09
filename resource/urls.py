from django.urls import path

from . import views, apis

app_name = 'resource'
urlpatterns = [
    path('upload_image/', views.UploadImageView.as_view(), name='upload_image'),
]
