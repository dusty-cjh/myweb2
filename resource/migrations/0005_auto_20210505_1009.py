# Generated by Django 3.1.8 on 2021-05-05 02:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0004_auto_20210503_1731'),
    ]

    operations = [
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.PositiveIntegerField(verbose_name='大小')),
                ('hash_val', models.SlugField(max_length=64, unique=True, verbose_name='哈希值')),
                ('hash_type', models.SlugField(default='sha256', max_length=10, verbose_name='哈希类型')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('link', models.SlugField(max_length=200, verbose_name='链接')),
                ('link_type', models.SmallIntegerField(choices=[(1, '图片'), (2, '视频'), (3, '音频')], verbose_name='链接类型')),
                ('format', models.CharField(max_length=10, verbose_name='格式')),
                ('status', models.SmallIntegerField(choices=[(0, '正常'), (1, '不可见'), (2, '删除')], default=1, verbose_name='状态')),
            ],
            options={
                'verbose_name': '物料',
                'verbose_name_plural': '物料',
            },
        ),
        migrations.AlterModelOptions(
            name='resource',
            options={'verbose_name': '资源', 'verbose_name_plural': '资源'},
        ),
    ]
