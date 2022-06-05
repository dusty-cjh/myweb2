from django import forms
from asgiref.sync import async_to_sync as a2s
from django.utils.translation import gettext as _
from .apis import AsyncOneBotApi


class OnebotGroupMultiChoiceField(forms.TypedMultipleChoiceField):
    help_text = _('hold `ctrl` in windows or hold `cmd` in macOS to select multiple fields')

    def __init__(self, *args, **kwargs):
        # get group list
        api = AsyncOneBotApi().with_cache(60).with_max_retry(3)
        group_list, err = a2s(api.get_group_list)()
        if err:
            raise RuntimeError('can not fetch group list, err={}, resp={}'.format(err, group_list))

        # create choices
        choices = [(x['group_id'], '{}({})'.format(x['group_name'], x['group_id'])) for x in group_list]

        # config super form
        kwargs['coerce'] = lambda val: int(val)
        kwargs['choices'] = choices
        kwargs['help_text'] = kwargs.get('help_text', self.help_text)
        super().__init__(*args, **kwargs)

