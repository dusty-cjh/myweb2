import json
from datetime import timedelta
from django.utils import timezone
from django.http.response import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, Http404, JsonResponse
from django.views.generic import TemplateView, View, ListView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.urls import reverse

from wechat.mixin import OAuthMixin, WeChatCommonMixin, WxViewContextMixin
from wechat.apis import WeChatPayResultMixin
from .models import VersionConfig, StudyCollect, PresentCollect


class SignUpBaseView(OAuthMixin, TemplateView):
	version = None
	template_name = 'collect/sign-up.html'

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		self.version = VersionConfig.objects.get(version=kwargs['version'])
		ctx.update({
			'version': self.version
		})
		return ctx


class SignUpView(SignUpBaseView):
	def get(self, request, *args, **kwargs):
		# 验证微信环境
		if not request.user.is_authenticated:
			return super().get(request, *args, **kwargs)

		try:
			version = VersionConfig.objects.get(version=kwargs['version'])
		except VersionConfig.DoesNotExist:
			return HttpResponse('<h1>该活动不存在</h1>')
		study = StudyCollect.objects.filter(Q(version=version.version) &
											Q(owner=request.user) & Q(status=StudyCollect.STATUS_PAYED))
		if len(study) > 0:
			url = reverse('collect:signup-source', args=(version.version,))
			return HttpResponseRedirect(redirect_to=url)

		return super().get(request, *args, **kwargs)


class SignUpResultView(WeChatPayResultMixin, View):

	@csrf_exempt
	def dispatch(self, request, *args, **kwargs):
		return super().dispatch(request, *args, **kwargs)

	def pay_valid(self, result):
		attach = json.loads(result['attach'])
		StudyCollect.objects.filter(id=attach['id']).update(status=StudyCollect.STATUS_PAYED,
															out_trade_no=result['out_trade_no'],
															cash_fee=result['cash_fee'])

	def pay_invalid(self, result):
		pass


class SignUpSourceView(SignUpBaseView):
	template_name = 'collect/signup-source.html'

	def get(self, request, *args, **kwargs):
		version = VersionConfig.objects.get(version=kwargs['version'])
		study = StudyCollect.objects.filter(Q(version=version.version) &
											Q(owner=request.user) & Q(status=StudyCollect.STATUS_PAYED))
		if len(study) == 0:
			return HttpResponseForbidden('您尚未参加该活动！')
		else:
			study = study[0]

		if study.status == StudyCollect.STATUS_PAYED:
			return super().get(request, *args, **kwargs)
		else:
			return HttpResponseForbidden('您尚未参加该活动！')


class PersonalListView(ListView):
	template_name = 'collect/personal-list.html'

	def get_queryset(self):
		if not self.request.user.is_authenticated:
			raise Http404("必须先进行登录")
		qs = StudyCollect.objects.filter(owner=self.request.user)
		return qs


class PresentView(OAuthMixin, WxViewContextMixin, TemplateView):
	template_name = 'collect/present.html'

	def post(self, request, *args, **kwargs):
		data = json.loads(request.body)
		obj = PresentCollect.objects.create(user=request.user, **data)
		data['created_time'] = obj.created_time
		return JsonResponse(data)


class PresentDownloadView(WeChatCommonMixin, WxViewContextMixin, TemplateView):
	template_name = 'collect/present_download.html'

	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		queryset = PresentCollect.objects.filter(created_time__gte=timezone.now() - timedelta(days=7))
		for obj in queryset:
			obj.previews_url = [WeChatCommonMixin.client.media.get_url(media_id)
								for media_id in obj.previews.split(';')[:-1]]
		ctx['object_list'] = queryset
		return ctx
