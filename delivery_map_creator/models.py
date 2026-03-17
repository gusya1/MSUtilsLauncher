from django.db import models
from root.models import SingletonModelMixin

from colorful.fields import RGBColorField

class DeliveryMapGeneratorSettings(SingletonModelMixin, models.Model):
    project_blacklist_dict = models.CharField(max_length=255, blank=True, verbose_name="Справочник с черным списком проектов")
    yandexmaps_key = models.CharField(max_length=255, blank=True, verbose_name="Ключ Яндекс.Карт")
    default_color = RGBColorField(blank=True, verbose_name="Цвет по умолчанию")
    delivery_time_missed_color = RGBColorField(blank=True, verbose_name="Цвет для пропущенного времени отгрузки")

    class Meta:
        verbose_name = "Настройки создания карты доставки"
        verbose_name_plural = "Настройки создания карты доставки"