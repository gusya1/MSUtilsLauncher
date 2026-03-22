from django.db import models
from root.models import SingletonModelMixin

from colorful.fields import RGBColorField

class DeliveryMapPaletteSettings(SingletonModelMixin, models.Model):
    delivery_order_attribute_name = models.CharField(max_length=255, blank=True, verbose_name="Название атрибута очередности доставки")

    class Meta:
        verbose_name = "Настройки палитры для выгрузки карты доставки"
        verbose_name_plural = "Настройки палитры для выгрузки карты доставки"

        permissions = [
            ("can_load_delivery_map", "Может загружать карту доставки"),
        ]


def get_yandex_maps_constructor_hotbar_colors():
    return [
        "#82cdff",
        "#1e98ff",
        "#177bc9",
        "#0e4779",
        "#ffd21e",
        "#ff931e",
        "#e6761b",
        "#ed4543",
        "#56db40",
        "#1bad03",
        "#97a100",
        "#595959",
        "#b3b3b3",
        "#f371d1",
        "#b51eff",
        "#793d0e",
    ]

class PaletteItem(models.Model):
    config = models.ForeignKey(
        DeliveryMapPaletteSettings,
        on_delete=models.CASCADE,
        related_name='project_by_color'
    )
    color = RGBColorField(verbose_name="Цвет", colors=get_yandex_maps_constructor_hotbar_colors())
    project = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Проект"
    )

    class Meta:
        unique_together = ['config', 'color', 'project'] 
        ordering = ['color'] 

    def __str__(self):
        return f"{self.color}: {self.project}"