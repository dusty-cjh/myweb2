import os
from django import forms
from django.conf import settings
from django.forms import widgets

from .models import Article


class ArticleAdminForm(forms.ModelForm):
    content = forms.CharField(widget=widgets.Textarea(attrs={
        'id': 'editor',
    }), label='正文')

    class Meta:
        model = Article
        fields = 'title content content_type author status'.split()

    class Media:
        js = ('/media/article/assets/js/ckeditor.js', '/media/js/run_editor.js')
