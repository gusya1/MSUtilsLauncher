import pydantic as pdt

from settings_manager import settings_manager


class DeliveryMapGeneratorSettings(pdt.BaseModel):
    projects_blacklist: str
    yandexmaps_key: str
    default_color: str
    delivery_time_missed_color: str


def get_delivery_map_generator_settings() -> DeliveryMapGeneratorSettings:
    return settings_manager.get_settings("delivery_map_generator", DeliveryMapGeneratorSettings)
