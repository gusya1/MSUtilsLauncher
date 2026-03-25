import re
import datetime

def get_re_group(reg_expr, string, group_index):
    result = re.search(reg_expr, string)
    if result is None:
        return None
    return result.group(group_index)

# Examples:
#  20:00 - 00:00
#  4 - 20:00
#  14-20
def strong_time_interval(string):
    result = re.search(r"((\d\d?)([:.](\d\d?))?)\s*-\s*+((\d\d?)([:.](\d\d?))?)", string)
    if result is None:
        return None
    try:
        return datetime.time(int(result.group(2)), int(result.group(4) or 0)), datetime.time(int(result.group(6)), int(result.group(8) or 0)) 
    except ValueError:
        return None

# Examples:
#  с 14:00
#  до 14:00
def humanable_time_interval(string):
    try:
        result = re.search(r"[сС]\s+((\d\d?)([:.](\d\d?))?)", string) or re.search(r"[пП][оО][сС][лЛ][еЕ]\s+((\d\d?)([:.](\d\d?))?)", string)
        start = None
        if result is not None:
            start = datetime.time(int(result.group(2)), int(result.group(4) or 0))
        result = re.search(r"[дДпП][оО]\s+((\d\d?)([:.](\d\d?))?)", string)
        end = None
        if result is not None:
            end = datetime.time(int(result.group(2)), int(result.group(4) or 0))
        return start, end
    except ValueError:
        return None

def parse_time_interval(string) -> tuple[datetime.time | None, datetime.time | None]:
    return strong_time_interval(string) or humanable_time_interval(string)

def parse_time_interval_safety(string: str) -> tuple[datetime.time, datetime.time]:
    start_time, end_time = parse_time_interval(string)
    if start_time is None:
        start_time = datetime.time.min
    if end_time is None:
        end_time = datetime.time.max
    if end_time < start_time:
        end_time = datetime.time.max
    return start_time, end_time
