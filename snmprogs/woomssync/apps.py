from django.apps import AppConfig
from root.apps import SnmAppBase


class WooMsSyncConfig(AppConfig, SnmAppBase):
    name = 'woomssync'
    verbose_name = "Синхронизация Woocommerce"
    display_in_menu = False
