from django.urls import path
from . import views

urlpatterns = [
    path("image_upload/", views.upload_file, name="upload_file"),
    path("example.md/", views.ExampleView.as_view(), name='example.md'),
]
