from django import forms

from .models import Content


class ContentAdminForm(forms.ModelForm):
	content = forms.CharField(required=True,
							  error_messages={'required': '不能为空！'},
							  widget=forms.widgets.Textarea(attrs={'rows': 10,
																   'cols': 100,
																   'placeholder': '输入回复内容 ...',
																   }),
							  )

	class Meta:
		model = Content
		fields = '__all__'
