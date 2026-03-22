from django.db import models
from root.models import SingletonModelMixin

class ProcessingCreatorSettings(SingletonModelMixin, models.Model):
    processing_plan_blacklist_dict = models.CharField(max_length=255, blank=True, verbose_name="Справочник c черным списком техкарт для автоматического производства")
    store_name = models.CharField(max_length=255, blank=True, verbose_name="Склад")

    class Meta:
        verbose_name = "Настройки создания тех.операций"
        verbose_name_plural = "Настройки создания тех.операций"

        permissions = [
            ("can_create_processing", "Может создавать тех.операции"),
        ]