import json
from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import widgets
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from ckeditor_uploader.fields import RichTextUploadingFormField

from manager.wechat_manager import upload_image
from .models import Goods, Order


class ExtraDataModelMixin:
    extra_fields = None

    def save(self, commit=True):
        #   check whether needs to parse extra data
        if self.extra_fields is None:
            return super().save(commit)

        extra_data = dict()
        for field_name in self.extra_fields:
            val = self.cleaned_data.get(field_name, None)
            if val:
                extra_data[field_name] = val
        self.cleaned_data['extra_data'] = json.dumps(extra_data)
        return super().save(commit)

    class Meta:
        exclude = ['extra_data', ]


class OrderModelForm(forms.ModelForm, ExtraDataModelMixin):
    extra_fields = 'logistics_information'.split()
    logistics_information = forms.CharField()

    class Meta:
        model = Order
        exclude = ['extra_data', ]


class GoodsModelForm(forms.ModelForm, ExtraDataModelMixin):
    preview = forms.ImageField()

    def save(self, commit=True):
        image = self.cleaned_data['preview']
        resp = upload_image(image)
        if resp.errcode != 0:
            raise ValueError("The %s could not be %s because uploading preview image is failed: code=%d,msg=%s" % (
                self.instance._meta.object_name,
                'created' if self.instance._state.adding else 'changed',
                resp.errcode,
                resp.errmsg,
            ))
        self.cleaned_data['preview'] = resp.url
        self.instance.preview = resp.url
        return super().save(commit=commit)

    class Meta:
        model = Goods
        exclude = ['extra_data', ]
        readonly_fields = ('html_preview_image', 'created_time',)
