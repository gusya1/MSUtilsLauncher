from django.apps import AppConfig
from root.apps import SnmAppBase


class DeliveryMapLoaderConfig(AppConfig, SnmAppBase):
    name = 'delivery_map_loader'
    verbose_name = "Выгрузка карты доставки"
    display_in_menu = True
