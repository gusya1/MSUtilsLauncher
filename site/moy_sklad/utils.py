

from datetime import datetime


def format_moy_sklad_datetime(dt: datetime):
    return dt.strftime('%Y-%m-%d %H:%M:%S')