from django.db import models


class CourierDataLoaderPermission(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ('can_load_courier_data', 'Может загружать данные курьеров'),
        )