# Generated by Django 3.2 on 2021-12-17 02:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0060_auto_20211130_2008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='address',
            field=models.CharField(max_length=100, verbose_name='Адрес'),
        ),
    ]
