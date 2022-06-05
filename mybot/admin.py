import ujson as json
from django.contrib import admin
from django import forms
from django.utils.translation import gettext as _
from bridge.onebot.django_extension import OnebotGroupMultiChoiceField
from .models import UserProfile, PluginConfigs, OneBotEventTab


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = 'name qq_number college grade college_student_number certificate ctime'.split()
    fields = 'name qq_number college grade college_student_number certificate'.split()


@admin.register(PluginConfigs)
class PluginConfigsAdmin(admin.ModelAdmin):
    list_display = ['name', 'verbose_name', 'ctime', ]
    fields = 'name verbose_name configs'.split()

    def get_form(self, request, obj: PluginConfigs = None, change=False, **kwargs):
        from .plugin_loader import get_plugin   # to avoid error of import when call django command
        if not change:
            return super().get_form(request, obj, change, **kwargs)

        # shrink fields to original data
        # json_form_data = obj.json_form_data
        plugin = get_plugin(obj.name)
        plugin_config = plugin.PluginConfig.from_db_config(obj)
        json_form_fields = plugin_config.json_form_fields()
        fields = kwargs.get('fields')
        if fields:
            fields = set(fields)
            for cfg_name in json_form_fields:
                if cfg_name in fields:
                    fields.remove(cfg_name)
            kwargs['fields'] = list(fields)

        # register form fields
        attrs = {}
        form = super().get_form(request, obj, change, **kwargs)
        for cfg_name in json_form_fields:
            cfg_field_class = getattr(plugin_config.__class__, cfg_name)
            cfg_val = getattr(plugin_config, cfg_name)
            form_field_kwargs = {
                'label': cfg_field_class.verbose_name,
                'required': False,
                'initial': cfg_val,
            }
            if cfg_field_class.django_form_field:
                form_field_class = cfg_field_class.django_form_field(**form_field_kwargs)
            else:
                if isinstance(cfg_val, int):
                    form_field_class = forms.IntegerField(**form_field_kwargs)
                elif isinstance(cfg_val, float):
                    form_field_class = forms.FloatField(**form_field_kwargs)
                elif isinstance(cfg_val, bool):
                    form_field_class = forms.BooleanField(**form_field_kwargs)
                elif isinstance(cfg_val, list):
                    form_field_class = OnebotGroupMultiChoiceField(**form_field_kwargs)
                else:
                    form_field_class = forms.CharField(**form_field_kwargs, widget=forms.Textarea(attrs=dict(cols=80)))
            attrs[cfg_name] = form_field_class
        json_form = type(form)(form.__name__.replace('Form', 'JsonForm'), (form,), attrs)

        # return new form
        return json_form

    def save_model(self, request, obj: PluginConfigs, form: forms.ModelForm, change):
        data = form.cleaned_data
        obj.configs = json.dumps(data)
        return super().save_model(request, obj, form, change)

    def get_fields(self, request, obj: PluginConfigs = None):
        from .plugin_loader import get_plugin   # to avoid error of import when call django command
        # fields = super().get_fields(request, obj)
        plugin = get_plugin(obj.name)
        plugin_config = plugin.PluginConfig.from_db_config(obj)
        fields = plugin_config.readonly_fields.copy()
        if obj is None:
            return fields

        fields_set = set(fields)
        json_form_fields = plugin_config.json_form_fields()
        for cfg_name in sorted(json_form_fields):
            if cfg_name not in fields_set:
                fields.append(cfg_name)
        return fields


@admin.register(OneBotEventTab)
class OneBotEventTabAdmin(admin.ModelAdmin):
    list_display = 'message_id post_type message_type sub_type group_id user_id anonymous time'.split()

