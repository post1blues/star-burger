# Generated by Django 3.2 on 2021-11-11 15:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0052_auto_20211111_1602'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='restaurant',
        ),
    ]
