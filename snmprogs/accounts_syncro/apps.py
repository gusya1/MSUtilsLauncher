from django.apps import AppConfig


class AccountsSyncroConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts_syncro'
    verbose_name = "Синхронизация расчётных счетов"
    is_snm_app = True
