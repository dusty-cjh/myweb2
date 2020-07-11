import os
import hashlib
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.conf import settings

from .models import Post


class PostAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget, label='正文')

    class Meta:
        model = Post
        fields = 'title content status'.split()
