import ujson as json
from django.contrib import admin
from django.db import models
from django import forms
from django.utils.translation import gettext as _
from .models import UserProfile, PluginConfigs


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = 'name qq_number college grade college_student_number certificate ctime'.split()
    fields = 'name qq_number college grade college_student_number certificate'.split()


@admin.register(PluginConfigs)
class PluginConfigsAdmin(admin.ModelAdmin):
    list_display = ['name', 'verbose_name', 'ctime', ]
    fields = 'name verbose_name configs'.split()

    def get_form(self, request, obj: PluginConfigs = None, change=False, **kwargs):
        if not change:
            return super().get_form(request, obj, change, **kwargs)

        # shrink fields to original data
        if not obj.json_form_data:
            obj.json_form_data = json.loads(obj.configs)
        json_form_data = obj.json_form_data
        fields = kwargs.get('fields')
        if fields:
            fields = set(fields)
            for cfg_name in json_form_data.keys():
                if cfg_name in fields:
                    fields.remove(cfg_name)
            kwargs['fields'] = list(fields)

        # create inner json form
        attrs = {}
        form = super().get_form(request, obj, change, **kwargs)
        for cfg_name, cfg_val in json_form_data.items():
            form_field_kwargs = {
                'label': cfg_name.replace('_', ' ').replace('-', ' '),
                'required': False,
                'initial': cfg_val,
            }
            if isinstance(cfg_val, int):
                form_field_class = forms.IntegerField(**form_field_kwargs)
            elif isinstance(cfg_val, float):
                form_field_class = forms.FloatField(**form_field_kwargs)
            elif isinstance(cfg_val, bool):
                form_field_class = forms.BooleanField(**form_field_kwargs)
            else:
                form_field_class = forms.CharField(**form_field_kwargs, widget=forms.Textarea(attrs=dict(cols=80)))
            attrs[cfg_name] = form_field_class
        json_form = type(form)(form.__name__.replace('Form', 'JsonForm'), (form,), attrs)

        # return new form
        return json_form

    def save_model(self, request, obj: PluginConfigs, form: forms.ModelForm, change):
        data = form.cleaned_data
        json_form_data = json.loads(obj.configs)
        for cfg_name in json_form_data.keys():
            if cfg_name in data:
                json_form_data[cfg_name] = data[cfg_name]
        obj.configs = json.dumps(json_form_data)
        return super().save_model(request, obj, form, change)

    def get_fields(self, request, obj: PluginConfigs = None):
        fields = super().get_fields(request, obj)
        if obj is None:
            return fields

        if not obj.json_form_data:
            obj.json_form_data = json.loads(obj.configs)
        fields_set = set(fields)
        for cfg_name in obj.json_form_data.keys():
            if cfg_name not in fields_set:
                fields.append(cfg_name)
        return fields
