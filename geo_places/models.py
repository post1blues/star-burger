from django.db import models
from django.utils import timezone
from django.conf import settings
import requests
from geopy import distance


class Address(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name='название')
    lat = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True, verbose_name='широта')
    lon = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True, verbose_name='долгота')
    requested_at = models.DateTimeField(default=timezone.now, verbose_name='дата создания')

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'

    def __str__(self):
        return self.title

    @staticmethod
    def fetch_coordinates(address):
        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": settings.YANDEX_APIKEY,
            "format": "json",
        })

        try:
            response.raise_for_status()
        except requests.HTTPError:
            return None

        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return lon, lat

    @staticmethod
    def calc_distance(start_pos, end_pos):
        return abs(round(distance.distance((end_pos.lat, end_pos.lon), (start_pos.lat, start_pos.lon)).km, 2))
