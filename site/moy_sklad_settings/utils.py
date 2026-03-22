from moy_sklad_settings.models import MoySkladSettings

def get_moy_sklad_token() -> str:
    settings =  MoySkladSettings.get_solo()
    if not settings:
        return None
    return settings.api_token