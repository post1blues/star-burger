from django.db.models import F
from django.http import JsonResponse
from django.templatetags.static import static
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order, OrderItem, Restaurant, RestaurantMenuItem
from .serializers import OrderSerializer


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['GET', 'POST'])
@transaction.non_atomic_requests
def register_order(request):
    response = {}

    if request.method == 'POST':
        serializer = OrderSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        order = Order.objects.create(
            firstname=serializer.validated_data['firstname'],
            lastname=serializer.validated_data['lastname'],
            phonenumber=serializer.validated_data['phonenumber'],
            address=serializer.validated_data['address']
        )

        products = [product['product'] for product in serializer.validated_data['products']]

        order_items = [OrderItem(
                order=order,
                quantity=product['quantity'],
                product=product['product'],
                price=product['product'].price
            ) for product in serializer.validated_data['products']]

        OrderItem.objects.bulk_create(order_items)

        menu_items = RestaurantMenuItem.objects.prefetch_related('restaurant').prefetch_related('product')\
            .filter(availability=True, product__in=products)

        available_restaurants = [menu_item.restaurant for menu_item in menu_items]

        order.restaurant = available_restaurants[0]
        order.save()

        response = OrderSerializer(order).data

    return Response(response)
