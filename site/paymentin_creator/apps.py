from django.apps import AppConfig
from root.apps import SnmAppBase


class PaymentinCreatorConfig(AppConfig, SnmAppBase):
    name = 'paymentin_creator'
    verbose_name = "Генератор входящих платежей"
    display_in_menu = True