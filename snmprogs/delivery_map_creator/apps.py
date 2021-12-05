from django.apps import AppConfig


class DeliveryMapCreatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'delivery_map_creator'
    verbose_name = "Генератор карты доставки"
    is_snm_app = True
