from django.apps import AppConfig

from root.apps import SnmAppBase


class CourierDataLoaderConfig(AppConfig, SnmAppBase):
    name = 'courier_data_loader'
    verbose_name = 'Загрузка данных курьеров'
