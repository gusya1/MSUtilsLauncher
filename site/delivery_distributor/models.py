import datetime
import logging

from django.db import models

from colorful.fields import RGBColorField

from root.models import SingletonModelMixin

logger = logging.getLogger("delivery_distributor")


class DeliveryRoutingSettings(SingletonModelMixin, models.Model):
    store_location = models.ForeignKey(
        "yandex_geocoder.Location",
        on_delete=models.CASCADE,
        verbose_name="Локация склада",
    )
    traffic_factor = models.FloatField(
        default=0.3,
        verbose_name="Коэффициент трафика",
        help_text="Система не учитывает пробки. Для получения картины более приближенной к реальности \
            время между двумя точками рассчитывается по формуле: time * (1 + traffic_factor)",
    )
    fuel_factor = models.FloatField(
        default=10,
        verbose_name="Расход топлива",
        help_text="Расход топлива на л/100 км",
    )
    start_service_time = models.DurationField(
        default=datetime.timedelta(minutes=30),
        verbose_name="Время на погрузку",
        help_text="Время необходимое на погрузку товаров на производстве",
    )
    order_service_time = models.DurationField(
        default=datetime.timedelta(minutes=15),
        verbose_name="Время на каждый заказ",
        help_text="Время необходимое на передачу заказа (парковка, лифт...)")
    max_waiting_time = models.DurationField(
        default=datetime.timedelta(hours=23, minutes=59),
        verbose_name="Максимальное время простоя курьера",
        help_text="Менять этот парамер нужно с ОСТОРОЖНОСТЬЮ. слишком маленькое значение может привести к неразрешимым конфликтам")
    max_time = models.DurationField(
        default=datetime.timedelta(hours=23, minutes=59),
        verbose_name="Максимальное время прибытия в конечную точку",
        help_text="Курьер НИ ПРИ КАКИХ ОБСТОЯТЕЛЬСТВАХ не может закончить позже этого врмени"
    )
    start_work_time = models.DurationField(
        default=datetime.timedelta(hours=6), 
        verbose_name="Время начала работы курьера (и производства)",
        help_text="При начале работы курьера раньше этого времени, будет назначаться штраф")
    end_work_time = models.DurationField(
        default=datetime.timedelta(hours=23, minutes=59), 
        verbose_name="Время окончания работы курьера",
        help_text="При окончании работы курьера позже этого времени, будет назначаться штраф")
    work_hours = models.DurationField(
        default=datetime.timedelta(hours=8), 
        verbose_name="Рабочие часы курьера", 
        help_text="При превышении общего времени работы курьера, будет назначаться штраф")
    max_late = models.DurationField(
        default=datetime.timedelta(hours=1), 
        verbose_name="Максимальное время опоздания к заказу", 
        help_text="Максимально возможное отклонение времени прибытия к заказу от назначенного интервала")
    vehicle_start_cost = models.IntegerField(
        default=10000, 
        verbose_name="Стоимость использования одной машины", 
        help_text="Используется для избегания коротких маршрутов")
    late_penalty = models.IntegerField(
        default=1000, 
        verbose_name="Штраф за опоздание", 
        help_text="Штраф решению за каждую секунду отклонения времени прибытия к заказу от назначенного инревала")
    slack_penalty = models.IntegerField(
        default=10, 
        verbose_name="Штраф за простой", 
        help_text="Штраф решению за каждую секунду простоя курьера")
    exceed_work_hours_penalty = models.IntegerField(
        default=100, 
        verbose_name="Штраф за превышение рабочих часов",
        help_text="Штраф решению за каждую секунду превышения рабочих часов")
    exceed_work_time_penalty = models.IntegerField(
        default=100, 
        verbose_name="Штраф за выход из рабочего времени",
        help_text="Штраф решению за каждую секунду отклонения времени работы курьера от рабочего времени"
    )
    exceed_capacity_penalty = models.IntegerField(
        default=10000, 
        verbose_name="Штраф за превышение вместимости",
        help_text="Штраф решению за каждый грамм превышения вместимости курьера"
    )
    max_process_time = models.DurationField(
        default=datetime.timedelta(minutes=5), 
        verbose_name="Максимальное время обработки маршрутов", 
        help_text="Система выдаст наилучший маршрут который смогла найти за предоставленное время")

    class Meta:
        verbose_name = "Настройки маршрутизации курьеров"
        verbose_name_plural = "Настройки маршрутизации курьеров"

        permissions = [
            ("can_make_delivery_routing", "Может создавать маршруты курьеров"),
        ]


def get_prefared_colors():
    return [
        "#82cdff",
        "#1e98ff",
        "#177bc9",
        "#0e4779",
        "#ffd21e",
        "#ff931e",
        "#e6761b",
        "#ed4543",
        "#56db40",
        "#1bad03",
        "#97a100",
        "#595959",
        "#b3b3b3",
        "#f371d1",
        "#b51eff",
        "#793d0e",
    ]

class Courier(models.Model):
    config = models.ForeignKey(
        DeliveryRoutingSettings, on_delete=models.CASCADE, related_name="couriers"
    )
    name = models.CharField(max_length=255, unique=True, verbose_name="Имя")
    color = RGBColorField(verbose_name="Цвет на карте", default="#000000", colors=get_prefared_colors())
    project = models.CharField(max_length=255, blank=True, verbose_name="Проект в МС")
    home_location = models.ForeignKey(
        "yandex_geocoder.Location",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name="Локация дом",
    )
    capacity = models.PositiveIntegerField(verbose_name="Вместимость (кг)")

    def __str__(self):
        return self.name
