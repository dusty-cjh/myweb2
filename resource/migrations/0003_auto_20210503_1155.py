# Generated by Django 3.1.8 on 2021-05-03 03:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource', '0002_resource_creator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='created_time',
            field=models.DateTimeField(auto_now_add=True, verbose_name='创建时间'),
        ),
    ]