from typing import Dict
from .settings import DeliveryMapPaletteSettings, write_palette, read_palette


def change_palette(project_by_color: Dict[str, str]):
    model = DeliveryMapPaletteSettings.model_validate({"palette": project_by_color})
    write_palette(model)

def get_projects_by_color():
    return read_palette().palette
