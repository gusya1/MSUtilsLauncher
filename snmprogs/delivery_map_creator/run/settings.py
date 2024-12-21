import pydantic as pdt

from settings_manager import settings_manager


class MoySkladAuthSettings(pdt.BaseModel):
    token: str


class DeliveryMapGeneratorSettings(pdt.BaseModel):
    projects_blacklist: str
    yandexmaps_key: str
    default_color: str
    delivery_time_missed_color: str


def get_moy_sklad_token() -> str:
    auth_settings = settings_manager.get_settings("moy_sklad_auth", MoySkladAuthSettings)
    return auth_settings.token

def get_delivery_map_generator_settings() -> DeliveryMapGeneratorSettings:
    return settings_manager.get_settings("delivery_map_generator", DeliveryMapGeneratorSettings)
