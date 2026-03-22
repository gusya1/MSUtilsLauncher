from django.db import models
from root.models import SingletonModelMixin

class YandexGeocoderSettings(SingletonModelMixin, models.Model):
    api_token = models.CharField(max_length=255, blank=True, verbose_name="Токен")
    
    class Meta:
        verbose_name = "Настройки Яндекс геокодера"
        verbose_name_plural = "Настройки Яндекс геокодера"

class Location(models.Model):
    address = models.CharField(max_length=512, unique=True, verbose_name="Адрес")
    longitude = models.FloatField(verbose_name="Долгота")
    latitude = models.FloatField(verbose_name="Широта")

    class Meta:
        verbose_name = "Локация"
        verbose_name_plural = "Локации"

    def __str__(self):
        return self.address
