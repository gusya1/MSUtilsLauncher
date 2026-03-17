import pydantic as pdt

from settings_manager import settings_manager


class ProcessingCreatorSettings(pdt.BaseModel):
    processing_plan_blacklist_entity: str
    store_name: str


def get_processing_creator_settings() -> ProcessingCreatorSettings:
    return settings_manager.get_settings("processing_creator", ProcessingCreatorSettings)