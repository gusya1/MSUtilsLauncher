from django.db import models


class CourierDataLoaderPermission(models.Model):
    class Meta:

        """Мета-настройки модели."""

        managed = False
        default_permissions = ()
        permissions = (
            ('can_load_courier_data', 'Может загружать данные курьеров'),
        )