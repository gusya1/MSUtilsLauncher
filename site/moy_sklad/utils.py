

from datetime import datetime, timedelta

from .model import MoySkladMetaField


def make_entity_meta_filed(entity):
    return MoySkladMetaField(meta=entity.meta)

def format_moy_sklad_datetime(dt: datetime):
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_one_day_filter(parameter, date):
    next_date = date + timedelta(days=1)
    return "{}>={};{}<{}".format(parameter, format_moy_sklad_datetime(date), parameter,
                                 format_moy_sklad_datetime(next_date))