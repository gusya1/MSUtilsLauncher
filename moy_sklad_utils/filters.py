import datetime

from MSApi import DateTimeFilter


def get_one_day_filter(parameter: str, date: datetime.datetime):
    return DateTimeFilter.gte(parameter, date) + DateTimeFilter.lt(parameter, date + datetime.timedelta(days=1))
