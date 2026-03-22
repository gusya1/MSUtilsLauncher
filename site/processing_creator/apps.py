from django.apps import AppConfig
from root.apps import SnmAppBase


class ProcessingCreatorConfig(AppConfig, SnmAppBase):
    name = 'processing_creator'
    verbose_name = "Генератор тех.операций"
    display_in_menu = True

