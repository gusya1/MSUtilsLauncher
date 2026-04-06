import logging
from urllib.parse import urlencode
from uuid import UUID
from typing import TypeVar
import json

from .exceptions import MoySkladError, UnauthorizedRequestError
from .client import MoySkladClient, make_url
from .types import get_link_to_entity_collection, get_response_class_by_base_class
from .model import MoySkladImage, MoySkladAttributeInfo, MoySkladState

logger = logging.getLogger("moysklad_sync")

T = TypeVar('T')

def get_entity_by_href(client: MoySkladClient, entity_class: type, href: str, **kwargs):
    response = client.get_by_href("{}?{}".format(href, urlencode(kwargs)))
    if response.status_code != 200:
        raise_for_status(response)
    return entity_class.model_validate(response.json())

def get_entities_by_href(client: MoySkladClient, entity_class: type, href: str, **kwargs) -> list:
    list_field = kwargs.pop("list_field", "rows")
    response = client.get_by_href("{}?{}".format(href, urlencode(kwargs)))
    if response.status_code != 200:
        raise_for_status(response)
    data = response.json()
    if isinstance(data, dict):
        data = data[list_field]
    return list(entity_class.model_validate(entity) for entity in data)

def walk_for_href(client: MoySkladClient, entity_class: type, href: str, **kwargs):
    offset = 0
    limit = kwargs.setdefault("limit", 1000)
    while True:
        kwargs["offset"] = offset
        entities = get_entities_by_href(client, entity_class, href, **kwargs)
        size = len(entities)
        offset += size
        for product in entities:
            yield product
        if size < limit:
            break

def walk_for_all(client: MoySkladClient, entity_class: type, **kwargs):
    return walk_for_href(client, entity_class, make_url(get_link_to_entity_collection(entity_class)), **kwargs)

def get_entity_by_id(client: MoySkladClient, entity_class: type[T], id: UUID) -> T | None:
    response = client.get_by_href(make_url("{}/{}".format(get_link_to_entity_collection(entity_class), id)))
    if response.status_code != 200:
        raise_for_status(response)
    return entity_class.model_validate(response.json())

def download_image(client: MoySkladClient, image: MoySkladImage):
    response = client.get_by_href(image.meta.downloadHref)
    if response.status_code != 200:
        raise_for_status(response)
    logger.debug("Image {} downloaded".format(image.filename))
    return response.content

def get_attibutes_for_entity(client: MoySkladClient, entity_class, **kwargs):
    return walk_for_href(client, MoySkladAttributeInfo, make_url("{}/metadata/attributes".format(get_link_to_entity_collection(entity_class))), **kwargs)

def get_states_for_entity(client: MoySkladClient, entity_class, **kwargs):
    return walk_for_href(client, MoySkladState, make_url("{}/metadata".format(get_link_to_entity_collection(entity_class))), list_field="states", **kwargs)

def get_entity_template(client: MoySkladClient, entity):
    response_class = get_response_class_by_base_class(type(entity))
    response = client.put("{}/new".format(get_link_to_entity_collection(response_class)), entity.model_dump_json(exclude_none=True))
    if response.status_code != 200:
        raise_for_status(response)
    return type(entity).model_validate(response.json())

def raise_for_status(response):
    if response.status_code == 401:
        raise UnauthorizedRequestError()
    if response.status_code in [412, 400]:
        raise MoySkladError(format_response_errors(response))
    response.raise_for_status()

def format_response_errors(response):
    return '\n'.join(error['error'] for error in response.json()['errors'])