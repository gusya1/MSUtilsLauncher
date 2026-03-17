import pydantic as pdt

from settings_manager import settings_manager


class MoySkladAuthSettings(pdt.BaseModel):
    token: str


def get_moy_sklad_token() -> str:
    auth_settings = settings_manager.get_settings("moy_sklad_auth", MoySkladAuthSettings)
    return auth_settings.token
