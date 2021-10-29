from django.db import models
from django.contrib.auth.models import AbstractUser


class MyUser(AbstractUser):
	SEX_MALE = 1
	SEX_FEMALE = 0
	SEX = (
		(SEX_FEMALE, '女',),
		(SEX_MALE, '男',),
	)

	openid = models.SlugField(max_length=32, default='', blank=True, verbose_name='OpenID')
	unionid = models.SlugField(max_length=32, default='', blank=True, verbose_name='UnionID')
	remark = models.CharField(max_length=20, default='', blank=True, verbose_name='用户标签')

	nickname = models.CharField(max_length=20, verbose_name='昵称', default='', blank=True)
	sex = models.SmallIntegerField(choices=SEX, default=SEX_MALE, verbose_name='性别')
	city = models.CharField(max_length=20, verbose_name='城市', default='', blank=True)
	province = models.CharField(max_length=10, verbose_name='省份', default='', blank=True)
	headimgurl = models.URLField(verbose_name='用户头像', default='', blank=True)

	class Meta:
		verbose_name = '用户'
		verbose_name_plural = '用户'
