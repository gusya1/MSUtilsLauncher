from django.db import models
from root.models import SingletonModelMixin

class AccountsSyncronizeSettings(SingletonModelMixin, models.Model):
    organization_name = models.CharField(max_length=255, blank=True, verbose_name="Название организации")
    states_and_accounts_dict = models.CharField(max_length=255, blank=True, verbose_name="Справочник соответствия статусов и счетов")

    class Meta:
        verbose_name = "Настройки синхорнизации счетов"
        verbose_name_plural = "Настройки синхорнизации счетов"

        permissions = [
            ("can_syncronize_accounts", "Может синхронизировать счета"),
        ]