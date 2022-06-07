import json
from django.db import models
from django.core.cache import cache
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext as _
# from django_ckeditor_5.fields import CKEditor5Field
from ckeditor_uploader.fields import RichTextUploadingField


class Goods(models.Model):
	STATUS_VISIBLE = 1
	STATUS_INVISIBLE = 2
	STATUS = (
		(STATUS_VISIBLE, '可见'),
		(STATUS_INVISIBLE, '不可见'),
	)

	title = models.CharField(verbose_name='标题', max_length=50)
	preview = models.CharField(verbose_name='商品预览', max_length=200)
	content = RichTextUploadingField(verbose_name='正文')
	fmt = models.CharField(verbose_name='正文格式', max_length=10, default='html', blank=True)
	status = models.PositiveSmallIntegerField(verbose_name='状态', choices=STATUS, default=STATUS_VISIBLE)
	created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True, editable=False)
	price = models.FloatField(verbose_name='价格')
	nums = models.PositiveIntegerField(verbose_name='库存', default=1)
	recommend = models.BooleanField(verbose_name='是否可被推荐', default=False)
	#
	pv = models.PositiveIntegerField(verbose_name='点击量', default=0)
	uv = models.PositiveIntegerField(verbose_name='浏览量', default=0)
	#
	extra_data = models.TextField(verbose_name=_('extra_data'))

	class Meta:
		verbose_name = verbose_name_plural = '商品'
		ordering = ['-uv', '-created_time']

	def __str__(self):
		return self.title

	@classmethod
	def latests(cls):
		return cls.objects.filter(models.Q(status=cls.STATUS_VISIBLE) &
								  models.Q(recommend=True) &
								  models.Q(nums__gt=0))

	@classmethod
	def handle_visit(cls, request, pk):
		uid = request.user.id
		increase_pv = False
		increase_uv = False

		pv_key = 'pv:{}:{}'.format(uid, request.path)
		uv_key = 'uv:{}:{}'.format(uid, request.path)

		if not cache.get(pv_key):
			increase_pv = True
			cache.set(pv_key, 1, 1 * 60)  # 1min 有效

		if not cache.get(uv_key):
			increase_uv = True
			cache.set(uv_key, 1, 24 * 60 * 60)

		if increase_uv and increase_pv:
			Goods.objects.filter(pk=pk).update(pv=models.F('pv') + 1, uv=models.F('uv') + 1)
		elif increase_pv:
			Goods.objects.filter(pk=pk).update(pv=models.F('pv') + 1)
		elif increase_uv:
			Goods.objects.filter(pk=pk).update(uv=models.F('uv') + 1)

	@property
	def html_preview_image(self):
		if not self.id:
			return ''
		url = reverse("shop:goods", args=(self.id,))
		return format_html('<a href="{}"><img src="{}" alt="{}" width="400px;" /></a>'.format(url, self.preview, url))


class Order(models.Model):
	STATUS_CREATED = 0
	STATUS_DEALING = 1
	STATUS_SENDING = 2
	STATUS_CANCEL = 3
	STATUS_REFUND = 4
	STATUS_FINISH = 5
	STATUS = (
		(STATUS_CREATED, '待付款'),
		(STATUS_DEALING, '待配送'),
		(STATUS_SENDING, '配送中'),
		(STATUS_CANCEL, '已取消'),
		(STATUS_REFUND, '拒收退款'),
		(STATUS_FINISH, '已确认收货'),
	)

	user = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name=_('Buyer'))
	goods = models.ForeignKey(Goods, on_delete=models.CASCADE, verbose_name='商品')
	nums = models.PositiveIntegerField(verbose_name='数量', default=1)
	total_fee = models.FloatField(verbose_name='总费用', default=0)
	payed = models.FloatField(verbose_name='实付款', default=0)
	address = models.CharField(verbose_name='收货地址', default='', max_length=200)
	out_trade_no = models.SlugField(max_length=32, verbose_name='微信后台订单号', default='')
	status = models.PositiveSmallIntegerField(verbose_name='状态', choices=STATUS, default=STATUS_CREATED)
	refund_reason = models.CharField(max_length=100, default='', blank=True, verbose_name='退款原因')
	created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
	extra_data = models.TextField(verbose_name='extra_data')

	class Meta:
		verbose_name = verbose_name_plural = '订单'
		ordering = ['-created_time', ]

	@property
	def status_display(self):
		return self.get_status_display()

	@property
	def logistics_information(self):
		data = getattr(self, '_extra_data', None)
		if data is None:
			try:
				data = json.loads(self.extra_data)
			except json.JSONDecodeError:
				data = dict()
			setattr(self, '_extra_data', data)
		return data.get('logistics_information', _('Current no logistics information'))


class Appraise(models.Model):
	STAR_SICK = 1
	STAR_BAD = 2
	STAR_NORMAL = 3
	STAR_GOOD = 4
	STAR_FANTASTIC = 5
	STAR = (
		(STAR_SICK, '★'),
		(STAR_BAD, '★★'),
		(STAR_NORMAL, '★★★'),
		(STAR_GOOD, '★★★★'),
		(STAR_FANTASTIC, '★★★★★'),
	)

	# 基本信息
	order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='订单')

	# 评分
	star = models.PositiveSmallIntegerField(verbose_name='评星', default=STAR_FANTASTIC, choices=STAR)
	content = models.CharField(verbose_name='评价内容', max_length=512, default='')
	created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

	def __str__(self):
		return str(self.star)

	class Meta:
		verbose_name = verbose_name_plural = '商品评价'
		ordering = ['-created_time', ]
