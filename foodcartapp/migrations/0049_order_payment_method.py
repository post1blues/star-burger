# Generated by Django 3.2 on 2021-11-11 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0048_auto_20211111_1420'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Наличные'), ('bank_card', 'Оплата картой')], default='cash', max_length=20),
        ),
    ]
