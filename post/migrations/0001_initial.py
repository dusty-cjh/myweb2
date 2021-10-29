# Generated by Django 3.1.4 on 2021-05-02 03:05

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Goods',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, verbose_name='标题')),
                ('content', models.TextField(verbose_name='正文')),
                ('status', models.PositiveSmallIntegerField(choices=[(1, '可见'), (2, '不可见')], default=1, verbose_name='状态')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('price', models.FloatField(verbose_name='价格')),
                ('previews', models.CharField(max_length=640, verbose_name='商品预览')),
                ('sales', models.PositiveIntegerField(default=0, verbose_name='销量')),
                ('nums', models.PositiveIntegerField(default=1, verbose_name='库存')),
            ],
            options={
                'verbose_name': '商品',
                'verbose_name_plural': '商品',
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, verbose_name='标题')),
                ('content', models.TextField(verbose_name='正文')),
                ('status', models.PositiveSmallIntegerField(choices=[(1, '可见'), (2, '不可见')], default=1, verbose_name='状态')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '文章',
                'verbose_name_plural': '文章',
            },
        ),
        migrations.CreateModel(
            name='Summary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.PositiveSmallIntegerField(choices=[(1, '文章'), (2, '照片'), (3, '视频'), (4, '音频'), (5, '商品')], verbose_name='类型')),
                ('url', models.CharField(max_length=200, verbose_name='链接')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('title', models.CharField(max_length=50, verbose_name='标题')),
                ('desc', models.CharField(blank=True, default='', max_length=200, verbose_name='描述')),
                ('recommend', models.BooleanField(default=False, help_text='如果作为推荐，则加入推荐系统', verbose_name='是否推荐')),
                ('mainpage', models.BooleanField(default=False, help_text='是否首页可见，否则只能在后台看到', verbose_name='是否首页可见')),
                ('preview', models.CharField(help_text='图/音视频', max_length=200, verbose_name='预览')),
                ('uv', models.PositiveIntegerField(default=0, verbose_name='Unique Visitor')),
                ('pv', models.PositiveIntegerField(default=0, verbose_name='Page View')),
            ],
            options={
                'verbose_name': '摘要',
                'verbose_name_plural': '摘要',
                'ordering': ['-created_time'],
            },
        ),
    ]
