# Generated by Django 3.1.1 on 2020-09-21 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proxies', '0004_auto_20200921_0925'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proxy',
            name='port',
            field=models.CharField(default=None, max_length=50),
        ),
    ]
