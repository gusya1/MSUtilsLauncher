from django.apps import AppConfig

from root.apps import SnmAppBase


class DeliveryDistributorConfig(AppConfig, SnmAppBase):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'delivery_distributor'
    verbose_name = "Маршрутизация курьеров"
    display_in_menu = True
