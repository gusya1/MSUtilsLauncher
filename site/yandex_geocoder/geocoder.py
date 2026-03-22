from django.conf import settings
from yandex_geocoder.client import Client
from yandex_geocoder.exceptions import NothingFonudError

from .models import Location

class Geocoder:
    def __init__(self):
        self.client = Client(settings.YANDEX_MAPS_API_KEY)

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
