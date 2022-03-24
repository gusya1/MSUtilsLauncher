from django.apps import AppConfig
from root.apps import SnmAppBase


class AccountsSyncConfig(AppConfig, SnmAppBase):
    name = 'accounts_syncro'
    verbose_name = "Синхронизация расчётных счетов"
    display_in_menu = True
