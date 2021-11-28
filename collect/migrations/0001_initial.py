# Generated by Django 3.2.7 on 2021-11-26 14:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VersionConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.CharField(max_length=20, unique=True, verbose_name='版本名称')),
                ('fee', models.FloatField(default=0, verbose_name='费用')),
                ('url', models.CharField(blank=True, default='', max_length=200, verbose_name='活动介绍链接')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('img', models.ImageField(blank=True, default='', max_length=200, upload_to='', verbose_name='加群二维码图片链接')),
            ],
            options={
                'verbose_name': '课程信息配置',
                'verbose_name_plural': '课程信息配置',
                'ordering': ['-created_time'],
            },
        ),
        migrations.CreateModel(
            name='StudyCollect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10, verbose_name='姓名')),
                ('school', models.CharField(max_length=10, verbose_name='专业班级')),
                ('age', models.PositiveSmallIntegerField(verbose_name='年龄')),
                ('sex', models.BooleanField(choices=[(1, '男'), (0, '女')], default=1, verbose_name='性别')),
                ('phone', models.SlugField(blank=True, default=0, verbose_name='手机')),
                ('ps', models.CharField(blank=True, default='', max_length=100, verbose_name='备注')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('status', models.PositiveSmallIntegerField(choices=[(0, '预付'), (1, '已付'), (2, '已退')], default=0, verbose_name='状态')),
                ('version', models.CharField(default='组队学习', help_text='例如：20年08月Python实验班', max_length=20, verbose_name='版本')),
                ('out_trade_no', models.SlugField(blank=True, default='', max_length=64, verbose_name='订单号')),
                ('cash_fee', models.FloatField(blank=True, default=0, verbose_name='实付款')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='微信用户ID')),
            ],
            options={
                'verbose_name': '组队学习报名',
                'verbose_name_plural': '组队学习报名',
                'ordering': ['-created_time'],
            },
        ),
        migrations.CreateModel(
            name='PresentCollect',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='', max_length=64)),
                ('previews', models.CharField(max_length=1024)),
                ('price', models.FloatField()),
                ('desc', models.CharField(default='', max_length=200)),
                ('name', models.CharField(default='', max_length=16)),
                ('addr', models.CharField(default='', max_length=128)),
                ('contact', models.CharField(max_length=64)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '商品信息收集',
                'verbose_name_plural': '商品信息收集',
                'ordering': ['-created_time'],
            },
        ),
    ]
