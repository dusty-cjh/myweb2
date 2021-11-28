# Generated by Django 3.2.7 on 2021-11-26 14:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_ckeditor_5.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Goods',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, verbose_name='标题')),
                ('preview', models.CharField(max_length=200, verbose_name='商品预览')),
                ('content', django_ckeditor_5.fields.CKEditor5Field(verbose_name='正文')),
                ('status', models.PositiveSmallIntegerField(choices=[(1, '可见'), (2, '不可见')], default=1, verbose_name='状态')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('price', models.FloatField(verbose_name='价格')),
                ('nums', models.PositiveIntegerField(default=1, verbose_name='库存')),
                ('recommend', models.BooleanField(default=False, verbose_name='是否可被推荐')),
                ('pv', models.PositiveIntegerField(default=0, verbose_name='点击量')),
                ('uv', models.PositiveIntegerField(default=0, verbose_name='浏览量')),
            ],
            options={
                'verbose_name': '商品',
                'verbose_name_plural': '商品',
                'ordering': ['-uv', '-created_time'],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nums', models.PositiveIntegerField(default=1, verbose_name='数量')),
                ('total_fee', models.FloatField(default=0, verbose_name='总费用')),
                ('payed', models.FloatField(default=0, verbose_name='实付款')),
                ('address', models.CharField(default='', max_length=200, verbose_name='收货地址')),
                ('out_trade_no', models.SlugField(default='', max_length=32, verbose_name='微信后台订单号')),
                ('status', models.PositiveSmallIntegerField(choices=[(0, '待付款'), (1, '待配送'), (2, '配送中'), (3, '已取消'), (4, '拒收退款'), (5, '已确认收货')], default=0, verbose_name='状态')),
                ('refund_reason', models.CharField(blank=True, default='', max_length=100, verbose_name='退款原因')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('goods', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.goods', verbose_name='商品')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='买家')),
            ],
            options={
                'verbose_name': '订单',
                'verbose_name_plural': '订单',
                'ordering': ['-created_time'],
            },
        ),
        migrations.CreateModel(
            name='Appraise',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('star', models.PositiveSmallIntegerField(choices=[(1, '★'), (2, '★★'), (3, '★★★'), (4, '★★★★'), (5, '★★★★★')], default=5, verbose_name='评星')),
                ('content', models.CharField(default='', max_length=512, verbose_name='评价内容')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.order', verbose_name='订单')),
            ],
            options={
                'verbose_name': '商品评价',
                'verbose_name_plural': '商品评价',
                'ordering': ['-created_time'],
            },
        ),
    ]
