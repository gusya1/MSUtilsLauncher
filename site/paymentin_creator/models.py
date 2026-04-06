from django.db import models

from root.models import SingletonModelMixin


class PaymentInCreatorSettings(SingletonModelMixin, models.Model):
    order_state = models.CharField(max_length=255, blank=True, verbose_name="Статус заказа по умолчанию")
    paymentin_state = models.CharField(max_length=255, blank=True, verbose_name="Статус создаваемого входящего платежа")

    class Meta:
        verbose_name = "Настройки создания входящих платежей"
        verbose_name_plural = "Настройки создания входящих платежей"

        permissions = [
            ("can_create_paymentin", "Может создавать входящие платежи"),
        ]