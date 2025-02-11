from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import F, Sum, Prefetch
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def annotate_with_order_price(self):
        order_price = Sum(F('items__quantity') * F('items__price'))
        order_items = OrderItem.objects.select_related('product')
        orders_with_prices = self.annotate(
            price=order_price
        ).prefetch_related(Prefetch('items', queryset=order_items))

        return orders_with_prices


class Order(models.Model):

    ORDER_STATUSES = [
        ('waiting', 'Необработанный'),
        ('in process', 'Готовится'),
        ('done', 'Сделан'),
        ('canceled', 'Отменен')
    ]

    PAYMENT_METHODS = [
        ('cash', 'Наличные'),
        ('bank_card', 'Оплата картой'),
        ('not_set', 'Не указано')
    ]

    firstname = models.CharField(max_length=50, verbose_name='Имя')
    lastname = models.CharField(max_length=50, verbose_name='Фамилия')
    phonenumber = PhoneNumberField(db_index=True, verbose_name='Телефон')
    address = models.CharField(max_length=100, verbose_name='Адрес')
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='ресторан',
        blank=True,
        null=True
    )
    payment_method = models.CharField(
        verbose_name='Способ оплаты',
        max_length=20,
        default='not_set',
        choices=PAYMENT_METHODS,
        db_index=True
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий к заказу')
    status = models.CharField(
        default='waiting',
        choices=ORDER_STATUSES,
        max_length=20,
        db_index=True,
        verbose_name='Сатус'
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='Создан в')
    called_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name='Позвонили в')
    delivered_at = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name='Доставлен в')

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return f'{self.firstname} {self.lastname} - {self.address}'

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ('-created_at',)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name='заказ'
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.CASCADE,
        verbose_name='продукт'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='количество'
    )
    price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        validators=[MinValueValidator(0)],
        verbose_name='цена'
    )

    def __str__(self):
        return f'Order: {self.id} - {self.product.name} ({self.quantity})'

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

