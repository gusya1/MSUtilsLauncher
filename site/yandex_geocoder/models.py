from django.db import models

class Location(models.Model):
    address = models.CharField(max_length=512, unique=True, verbose_name="Адрес")
    longitude = models.FloatField(verbose_name="Долгота")
    latitude = models.FloatField(verbose_name="Широта")

    class Meta:
        verbose_name = "Локация"
        verbose_name_plural = "Локации"

    def __str__(self):
        return self.address
