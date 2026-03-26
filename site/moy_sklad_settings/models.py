from django.db import models
from root.models import SingletonModelMixin

class MoySkladSettings(SingletonModelMixin, models.Model):
    api_token = models.CharField(max_length=255, blank=True, verbose_name="Токен")
    delivery_order_attribute_name = models.CharField(max_length=255, blank=True, verbose_name="Название атрибута очередности доставки")
    
    class Meta:
        verbose_name = "Настройки Мой Склад"
        verbose_name_plural = "Настройки Мой Склад"