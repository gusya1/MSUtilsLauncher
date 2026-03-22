import logging

from django.db import models
from root.models import SingletonModelMixin


logger = logging.getLogger("delivey_distributor")

class DeliveryRoutingSettings(SingletonModelMixin, models.Model):
    store_location = models.ForeignKey('yandex_geocoder.Location', on_delete=models.CASCADE, verbose_name="Локация склада")

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
    home_location = models.ForeignKey('yandex_geocoder.Location', null=True, on_delete=models.CASCADE, verbose_name="Локация дом")
    capacity = models.PositiveIntegerField(verbose_name="Вместимость (кг)")

    def __str__(self):
        return self.name