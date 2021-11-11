from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
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


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    menu_items = RestaurantMenuItem.objects.prefetch_related('restaurant')\
                                           .prefetch_related('product')\
                                           .filter(availability=True)

    orders = Order.objects.filter(status='waiting')\
                          .annotate_with_order_price()

    for order in orders:
        order_products = [order_item.product for order_item in order.items.all().distinct()]
        available_restaurants = [menu_item.restaurant for menu_item in menu_items.filter(product__in=order_products)]
        order.restaurants = available_restaurants

        addresses = Address.objects.all()
        addresses_to_create = []

        order_address = None
        for address in addresses:
            if address.title == order.address:
                order_address = address
                break

        if not order_address:
            order_address_pos = Address.fetch_coordinates(order.address)
            order_address = Address(
                title=order.address,
                lon=order_address_pos[0],
                lat=order_address_pos[1]
            )
            addresses_to_create.append(order_address)

        for restaurant in order.restaurants:
            restaurant_address = None
            for address in addresses:
                if restaurant.address == address.title:
                    restaurant_address = address
                    break

            if not restaurant_address:
                restaurant_pos = Address.fetch_coordinates(restaurant.address)
                restaurant_address = Address(
                    title=restaurant.address,
                    lon=restaurant_pos[0],
                    lat=restaurant_pos[1]
                )
                addresses_to_create.append(restaurant_address)
            restaurant.order_distance = Address.calc_distance(restaurant_address, order_address)

        Address.objects.bulk_create(addresses_to_create)

        order.restaurants = sorted(order.restaurants, key=lambda x: x.order_distance)

    return render(request, template_name='order_items.html', context={
        'orders': orders
    })
