import os
from django import forms
from django.conf import settings
from django.forms import widgets
from django.contrib.auth.models import User
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import Article


class ArticleAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget(), label='正文')
    content_type = forms.CharField(widget=forms.widgets.HiddenInput())
    author = forms.ModelChoiceField(
        User.objects.filter(is_staff=True),
        widget=forms.widgets.HiddenInput(),
        required=False,
        blank=True,
    )

    def __init__(self, *args, **kwargs):
        # specify default value
        if not kwargs.get('instance'):
            kwargs['initial'] = {
                'content_type': Article.TYPE_HTML,
            }

        super().__init__(*args, **kwargs)

    class Meta:
        model = Article
        fields = 'title content content_type author status'.split()

    def is_valid(self):
        return super().is_valid()

    def clean_content_type(self):
        content_type = int(self.cleaned_data['content_type'])
        if content_type != Article.TYPE_HTML:
            raise forms.ValidationError(
                'only support html',
                19
            )
        return content_type
