from yandex_geocoder.client import Client
from yandex_geocoder.exceptions import NothingFonudError

from .models import YandexGeocoderSettings, Location

class Geocoder:
    def __init__(self):
        self.client = Client(YandexGeocoderSettings.get_solo().api_token)

    def geocode(self, address):
        if not address:
            return None
        try:
            return Location.objects.get(address=address)
        except Location.DoesNotExist:
            pass
        try:
            lon_lat = self.client.get_coordinates(address)
            return Location.objects.create(address=address, longitude=lon_lat[0], latitude=lon_lat[1])
        except NothingFonudError:
            return None
