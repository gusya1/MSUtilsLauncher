import logging
from requests import Session
from requests.adapters import HTTPAdapter, Retry
import urllib.parse
from ratelimit import limits, sleep_and_retry
from typing import Callable
import functools

logger = logging.getLogger("moysklad_sync")

def _create_session():
    session = Session()
    session.mount('https://',
                  HTTPAdapter(max_retries=Retry(total=10, status_forcelist=[500, 503])))
    return session

def make_url(request: str):
    ms_url = "https://api.moysklad.ru/api/remap/1.2"
    return f"{ms_url}/{request}"

# Декоратор для rate limiting
def rate_limited(calls: int = 45, period: int = 3):
    """
    Декоратор для ограничения количества вызовов.
    Не более `calls` вызовов за `period` секунд.
    """
    def decorator(func: Callable) -> Callable:
        @sleep_and_retry
        @limits(calls=calls, period=period)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

class MoySkladClient:
    def __init__(self, token: str | None = None):
        self.__token = token
        self.__session = _create_session()

    def set_token(self, token: str):
        self.__token = token

    def authenticated(self):
        return self.__token is not None

    @rate_limited()
    def post(self, request, data, **kwargs):
        request = urllib.parse.quote(request)
        logger.debug("MoySklad POST: %s", make_url(request))
        return self.__session.post(make_url(request), data, headers=self.__make_auth_headers(), **kwargs)

    def get(self, request, **kwargs):
        request = urllib.parse.quote(request)
        logger.debug("MoySklad GET: %s", make_url(request))
        return self.get_by_href(make_url(request), **kwargs)

    @rate_limited()
    def put(self, request, data, **kwargs):
        request = urllib.parse.quote(request)
        logger.debug("MoySklad PUT: %s", make_url(request))
        return self.__session.put(make_url(request), data, headers=self.__make_auth_headers(), **kwargs)

    @rate_limited()
    def get_by_href(self, href, **kwargs):
        return self.__session.get(href, headers=self.__make_auth_headers(), **kwargs)

    def __make_auth_headers(self):
        return {
            "Authorization": f"Bearer {self.__token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip"
        }