import logging

from .types import get_link_to_entity_update, get_response_class_by_base_class
from .getters import raise_for_status
from .client import MoySkladClient

logger = logging.getLogger("moysklad_sync")

def update_entity(client: MoySkladClient, id, entity_base):
    response = client.put(get_link_to_entity_update(type(entity_base), id), entity_base.model_dump_json(exclude_none=True))
    if response.status_code != 200:
        raise_for_status(response)
    return get_response_class_by_base_class(type(entity_base)).model_validate(response.json())