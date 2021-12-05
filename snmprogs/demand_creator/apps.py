from django.apps import AppConfig


class DemandCreatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'demand_creator'
    verbose_name = "Генератор отгрузок"
    is_snm_app = True
