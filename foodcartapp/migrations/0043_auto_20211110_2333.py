# Generated by Django 3.2 on 2021-11-10 21:33

from django.db import migrations


def count_order_price(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    for order_item in OrderItem.objects.all():
        order_item.price = order_item.quantity * order_item.product.price
        order_item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0042_orderitem_price'),
    ]

    operations = [
        migrations.RunPython(count_order_price)
    ]
