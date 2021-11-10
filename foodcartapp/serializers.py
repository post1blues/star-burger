from rest_framework.serializers import ModelSerializer
from phonenumber_field.serializerfields import PhoneNumberField

from foodcartapp.models import Order, OrderItem


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['quantity', 'product']


class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)
    phonenumber = PhoneNumberField()

    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'products']


