from django.apps import AppConfig


class ProcessingCreatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'processing_creator'
    verbose_name = "Генератор тех.операций"
    is_snm_app = True
