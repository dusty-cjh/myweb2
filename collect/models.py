from django.db import models


class StudyCollect(models.Model):
	SEX_MALE = 1
	SEX_FEMALE = 0
	SEX = (
		(SEX_MALE, '男'),
		(SEX_FEMALE, '女'),
	)

	STATUS_PREPAY = 0
	STATUS_PAYED = 1
	STATUS_REFUND = 2
	STATUS = (
		(STATUS_PREPAY, '预付'),
		(STATUS_PAYED, '已付'),
		(STATUS_REFUND, '已退'),
	)

	name = models.CharField(verbose_name='姓名', max_length=10)
	school = models.CharField(verbose_name='专业班级', max_length=10)
	age = models.PositiveSmallIntegerField(verbose_name='年龄')
	sex = models.BooleanField(verbose_name='性别', choices=SEX, default=SEX_MALE)
	phone = models.SlugField(verbose_name='手机', default=0, blank=True)
	ps = models.CharField(verbose_name='备注', default='', max_length=100, blank=True)
	created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

	owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='微信用户ID', null=True, blank=True)
	status = models.PositiveSmallIntegerField(verbose_name='状态', choices=STATUS, default=STATUS_PREPAY)
	version = models.CharField(verbose_name='版本', max_length=20, default='组队学习', help_text='例如：20年08月Python实验班')
	out_trade_no = models.SlugField(verbose_name='订单号', max_length=64, default='', blank=True)
	cash_fee = models.FloatField(verbose_name='实付款', default=0, blank=True)

	class Meta:
		verbose_name = verbose_name_plural = '组队学习报名'
		ordering = ['-created_time']

	def __str__(self):
		return self.name


class VersionConfig(models.Model):
	version = models.CharField(verbose_name='版本名称', max_length=20, unique=True)
	fee = models.FloatField(verbose_name='费用', default=0)
	url = models.CharField(verbose_name='活动介绍链接', max_length=200, default='', blank=True)
	created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
	img = models.ImageField(verbose_name='加群二维码图片链接', max_length=200, default='', blank=True)

	class Meta:
		verbose_name = verbose_name_plural = '课程信息配置'
		ordering = ['-created_time']

	def __str__(self):
		return '{}(￥{})'.format(self.version, self.fee)


class PresentCollect(models.Model):
	title = models.CharField(max_length=64, default="")
	previews = models.CharField(max_length=1024)
	price = models.FloatField()
	desc = models.CharField(max_length=200, default="")
	name = models.CharField(max_length=16, default="")
	addr = models.CharField(max_length=128, default="")
	contact = models.CharField(max_length=64)
	created_time = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)

	class Meta:
		verbose_name = verbose_name_plural = '商品信息收集'
		ordering = ['-created_time', ]
