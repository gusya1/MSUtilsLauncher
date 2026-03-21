from django.db import models
from root.models import SingletonModelMixin

from colorful.fields import RGBColorField


class Location(models.Model):
    address = models.CharField(max_length=512, unique=True, verbose_name="Адрес")
    longitude = models.FloatField(verbose_name="Долгота")
    latitude = models.FloatField(verbose_name="Широта")

    class Meta:
        verbose_name = "Локация"
        verbose_name_plural = "Локации"

    def __str__(self):
        return self.address

class DeliveryRoutingSettings(SingletonModelMixin, models.Model):
    store_location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Локация склада")

    class Meta:
        verbose_name = "Настройки маршрутизации курьеров"
        verbose_name_plural = "Настройки маршрутизации курьеров"

        permissions = [
            ("can_make_delivery_routing", "Может создавать маршруты курьеров"),
        ]

class Courier(models.Model):
    config = models.ForeignKey(
        DeliveryRoutingSettings,
        on_delete=models.CASCADE,
        related_name='couriers'
    )
    name = models.CharField(max_length=255, unique=True, verbose_name="Имя")
    home_location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Локация дом")
    capacity = models.PositiveIntegerField(verbose_name="Вместимость (кг)")

    def __str__(self):
        return self.name