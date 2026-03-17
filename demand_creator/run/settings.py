import pydantic as pdt

from settings_manager import settings_manager

class DemandCreatorSettings(pdt.BaseModel):
    projects_blacklist_entity: str


def get_demand_creator_settings() -> DemandCreatorSettings:
    return settings_manager.get_settings("demand_creator", DemandCreatorSettings)