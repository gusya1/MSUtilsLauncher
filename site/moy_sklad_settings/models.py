from django.db import models
from root.models import SingletonModelMixin


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

    class Meta:
        verbose_name = "Настройки Мой Склад"
        verbose_name_plural = "Настройки Мой Склад"
