from django.db import models
from root.models import SingletonModelMixin

from django.contrib.postgres.fields import ArrayField




class MoySkladSettings(SingletonModelMixin, models.Model):
    api_token = models.CharField(max_length=255, blank=True, verbose_name="Токен")
    delivery_order_attribute_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Название дополнительного поля очередности доставки",
        help_text="Дополнительное поле заказа покупателя",
    )
    delivery_time_attribute_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Название дополнительного поля времени доставки",
        help_text="Дополнительное поле заказа покупателя",
    )

    @property
    def delivery_routing_project_blacklist(self):
        return list(
            self.project_blacklist_for_delivery_routing.values_list("value", flat=True)
        )

    class Meta:
        verbose_name = "Настройки Мой Склад"
        verbose_name_plural = "Настройки Мой Склад"


class BlacklistProjectMS(models.Model):
    settings = models.ForeignKey(
        MoySkladSettings,
        on_delete=models.CASCADE,
        related_name="project_blacklist_for_delivery_routing"
    )
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.value

    class Meta:
        verbose_name = "Проект МС"
        verbose_name_plural = "Черный список проектов для маршрутизации курьеров"