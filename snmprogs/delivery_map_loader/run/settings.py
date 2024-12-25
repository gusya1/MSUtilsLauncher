import pydantic as pdt

from settings_manager import settings_manager


ColorCode = pdt.constr(pattern=r"#[abcdef1234567890]{6}")


class DeliveryMapPaletteSettings(pdt.BaseModel):
    palette: dict[ColorCode, str]


def write_palette(palette: DeliveryMapPaletteSettings):
    settings_manager.write_settings_group("delivery_map_palette", palette)

def read_palette() -> DeliveryMapPaletteSettings:
    return settings_manager.get_settings("delivery_map_palette", DeliveryMapPaletteSettings)
