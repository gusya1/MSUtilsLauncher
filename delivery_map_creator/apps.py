from django.apps import AppConfig
from root.apps import SnmAppBase


class DeliveryMapCreatorConfig(AppConfig, SnmAppBase):
    name = 'delivery_map_creator'
    verbose_name = "Генератор карты доставки"
    display_in_menu = True
