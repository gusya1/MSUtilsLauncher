from django.db import models
from root.models import SingletonModelMixin

class DemandCreatorSettings(SingletonModelMixin, models.Model):
    project_blacklist_dict = models.CharField(max_length=255, blank=True, verbose_name="Справочник с черным списком проектов")

    class Meta:
        verbose_name = "Настройки создания отгрузок"
        verbose_name_plural = "Настройки создания отгрузок"