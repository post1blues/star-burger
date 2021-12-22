from django import forms
from django.db.models import Subquery, OuterRef, Prefetch
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem, OrderItem
from geo_places.models import Address


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def serialize_order(order):
    return {
        'id': order.id,
        'status': order.get_status_display(),
        'price': order.price,
        'payment_method': order.get_payment_method_display(),
        'firstname': order.firstname,
        'lastname': order.lastname,
        'phonenumber': order.phonenumber,
        'address': order.address,
        'comment': order.comment,
        'restaurants': sorted(order.restaurants, key=lambda x: x.order_distance)[:10],
    }


def create_address(address):
    address_to_create = None
    coordinates = Address.fetch_coordinates(address)

    if coordinates:
        lon, lat = coordinates
        address_to_create = Address(
            title=address,
            lon=lon,
            lat=lat
        )
    return address_to_create


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):

    addresses = {address.title: address for address in Address.objects.all()}

    orders = Order.objects.select_related('restaurant')\
        .annotate_with_order_price()\
        .filter(status='waiting')

    menu_items = list(RestaurantMenuItem.objects.select_related('restaurant')\
        .select_related('product')\
        .filter(availability=True))

    addresses_to_create = []

    for order in orders:
        order.restaurants = []
        available_restaurants = []

        for item in order.items.all():
            item_restaurants = [menu_item.restaurant for menu_item in menu_items if item.product == menu_item.product]
            available_restaurants.extend(item_restaurants)

        available_restaurants = list(set(available_restaurants))
        order_db_address = addresses.get(order.address)

        if not order_db_address:
            order_db_address = create_address(order.address)
            if order_db_address:
                addresses_to_create.append(order_db_address)

        for restaurant in available_restaurants:
            if not restaurant.address:
                continue

            restaurant_db_address = addresses.get(restaurant.address)
            if not restaurant_db_address:
                restaurant_db_address = create_address(restaurant.address)

                if not restaurant_db_address:
                    continue

                addresses_to_create.append(restaurant_db_address)
                addresses[restaurant_db_address.title] = restaurant_db_address

            order_distance = Address.calc_distance(restaurant_db_address, order_db_address)

            if order_distance:
                restaurant.order_distance = order_distance
                order.restaurants.append(restaurant)

    Address.objects.bulk_create(addresses_to_create)
    context = {'orders': [serialize_order(order) for order in orders]}

    return render(request, template_name='order_items.html', context=context)
