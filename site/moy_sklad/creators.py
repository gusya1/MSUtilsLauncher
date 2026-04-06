from .model import MoySkladMetaField
from .types import get_link_to_entity_create, get_response_class_by_create_class
from .getters import raise_for_status
from .client import MoySkladClient


def create_entity(client: MoySkladClient, entity):
    response = client.post(get_link_to_entity_create(type(entity)), entity.model_dump_json(exclude_none=True))
    if response.status_code != 200:
        raise_for_status(response)
    return get_response_class_by_create_class(type(entity)).model_validate(response.json())

def make_entity_meta_filed(entity):
    return MoySkladMetaField(meta=entity.meta)