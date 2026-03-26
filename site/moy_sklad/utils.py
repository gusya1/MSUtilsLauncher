

from datetime import datetime

from .model import MoySkladMetaField


def make_entity_meta_filed(entity):
    return MoySkladMetaField(meta=entity.meta)

def format_moy_sklad_datetime(dt: datetime):
    return dt.strftime('%Y-%m-%d %H:%M:%S')