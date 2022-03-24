from django.apps import AppConfig
from root.apps import SnmAppBase


class DemandCreatorConfig(AppConfig, SnmAppBase):
    name = 'demand_creator'
    verbose_name = "Генератор отгрузок"
    display_in_menu = True
