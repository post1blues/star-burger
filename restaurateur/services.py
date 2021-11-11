import requests
from geopy import distance
from django.conf import settings


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


def calc_distance(start_pos, end_pos):
    return abs(round(distance.distance(end_pos, start_pos).km, 2))
