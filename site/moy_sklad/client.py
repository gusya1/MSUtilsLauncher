import logging
import math
import random
import time
import urllib.parse
import functools
from requests import Session
import requests
from requests.adapters import HTTPAdapter, Retry
from ratelimit import limits, sleep_and_retry
from collections.abc import Callable

from .exceptions import MoySkladConnectionError, MoySkladRateLimitError

logger = logging.getLogger("moysklad_sync")

# Лимит запросов JSON API МойСклада для user-токена (Bearer): 11 запросов/3с.
# Расписание изменения веса запроса для user-токена:
#   с 01.09.2026 — вес 3 → 15 запросов/3с;
#   с 01.12.2026 — вес 4 → 11 запросов/3с (финальное значение).
# Заложено финальное значение: безопасно на оба периода
# (до 01.12.2026 клиент просто чуть медленнее, чем позволяет лимит).
DEFAULT_RATE_LIMIT_CALLS = 11
DEFAULT_RATE_LIMIT_PERIOD = 3

# Повторы при HTTP 429: до RATE_LIMIT_MAX_RETRIES повторов на запрос;
# sleep = max(значение из заголовков X-Lognex-Retry-After / X-Lognex-Reset (мс),
#             экспоненциальный backoff с джиттером).
# Ограниченность критична: более 200 запросов с ошибкой 429 за минуту
# ведут к автоматическому отключению доступа к API.
RATE_LIMIT_MAX_RETRIES = 5
RETRY_BASE_BACKOFF_SECONDS = 1.0
RETRY_JITTER_SECONDS = 0.5

def _create_session():
    session = Session()
    session.mount('https://',
                  HTTPAdapter(max_retries=Retry(total=10, status_forcelist=[500, 503])))
    return session

def make_url(request: str):
    ms_url = "https://api.moysklad.ru/api/remap/1.2"
    return f"{ms_url}/{request}"

# Общий лимитер на все HTTP-методы клиента (post/put/get_by_href):
# МойСклад считает лимит запросов по токену, а не по методу.
_client_limiter = limits(calls=DEFAULT_RATE_LIMIT_CALLS, period=DEFAULT_RATE_LIMIT_PERIOD)

def rate_limited(limiter=None):
    """
    Декоратор для ограничения количества вызовов.

    Если limiter не передан — создаётся новый независимый лимитер:
    не более DEFAULT_RATE_LIMIT_CALLS вызовов за DEFAULT_RATE_LIMIT_PERIOD секунд.
    """
    if limiter is None:
        limiter = limits(calls=DEFAULT_RATE_LIMIT_CALLS, period=DEFAULT_RATE_LIMIT_PERIOD)
    def decorator(func: Callable) -> Callable:
        @sleep_and_retry
        @limiter
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def connection_error_rerise():
    """Декоратор: оборачивает requests ConnectionError в MoySkladConnectionError."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ConnectionError as e:
                raise MoySkladConnectionError(str(e))
        return wrapper
    return decorator

def retry_delay_seconds(response, attempt: int) -> float:
    """
    Время сна (секунды) перед повтором запроса после HTTP 429.

    max(значение из заголовков X-Lognex-Retry-After / X-Lognex-Reset (мс → с),
        экспоненциальный backoff с джиттером).
    X-Lognex-Reset == 0 означает, что ограничение не установлено —
    в этом случае учитывается только backoff.
    Некорректные значения ("nan", "inf") игнорируются.
    """
    header_delay = 0.0
    for name in ("X-Lognex-Retry-After", "X-Lognex-Reset"):
        raw = response.headers.get(name)
        if raw is None:
            continue
        try:
            ms = float(raw)
        except ValueError:
            continue
        if not math.isfinite(ms):
            continue
        header_delay = max(header_delay, ms / 1000.0)
    backoff = RETRY_BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0, RETRY_JITTER_SECONDS)
    return max(header_delay, backoff)

def _format_rate_limit_headers(response) -> str:
    """
    Заголовки ответа про лимит запросов для логирования.

    Отсутствующие заголовки показываются как "-".
    """
    parts = []
    for name in ("X-RateLimit-Remaining", "X-Lognex-Retry-After", "X-Lognex-Reset"):
        value = response.headers.get(name)
        parts.append("{}={}".format(name, "-" if value is None else value))
    return ", ".join(parts)

class MoySkladClient:
    def __init__(self, token: str | None = None):
        self.__token = token
        self.__session = _create_session()

    def set_token(self, token: str):
        self.__token = token

    def authenticated(self):
        return self.__token is not None

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        HTTP-запрос с повтором при 429 (лимит запросов МойСклада).

        Повтор после 429 безопасен для всех методов, включая POST:
        429 означает, что запрос отклонён сервером по лимиту и не был обработан
        (в отличие от таймаута/обрыва соединения, где обработка могла начаться),
        поэтому дублей при повторе не возникает.
        После исчерпания повторов — MoySkladRateLimitError.
        """
        headers = self.__make_auth_headers()
        for attempt in range(RATE_LIMIT_MAX_RETRIES + 1):
            response = self.__session.request(method, url, headers=headers, **kwargs)
            if response.status_code != 429:
                return response
            if attempt < RATE_LIMIT_MAX_RETRIES:
                delay = retry_delay_seconds(response, attempt)
                logger.warning("MoySklad HTTP 429 (rate limit), %s %s, повтор %d/%d через %.2fs; %s",
                               method, url, attempt + 1, RATE_LIMIT_MAX_RETRIES, delay,
                               _format_rate_limit_headers(response))
                time.sleep(delay)
        logger.error("Лимит запросов МойСклада исчерпан после %d повторов: %s",
                     RATE_LIMIT_MAX_RETRIES, url)
        raise MoySkladRateLimitError(
            "Лимит запросов МойСклада исчерпан после {} повторов: {}".format(RATE_LIMIT_MAX_RETRIES, url)
        )

    @rate_limited(_client_limiter)
    @connection_error_rerise()
    def post(self, request, data, **kwargs):
        request = urllib.parse.quote(request)
        logger.debug("MoySklad POST: %s", make_url(request))
        return self._request("POST", make_url(request), data=data, **kwargs)

    def get(self, request, **kwargs):
        request = urllib.parse.quote(request)
        logger.debug("MoySklad GET: %s", make_url(request))
        return self.get_by_href(make_url(request), **kwargs)

    @rate_limited(_client_limiter)
    @connection_error_rerise()
    def put(self, request, data, **kwargs):
        request = urllib.parse.quote(request)
        logger.debug("MoySklad PUT: %s", make_url(request))
        return self._request("PUT", make_url(request), data=data, **kwargs)

    @rate_limited(_client_limiter)
    @connection_error_rerise()
    def get_by_href(self, href, **kwargs):
        return self._request("GET", href, **kwargs)

    def __make_auth_headers(self):
        return {
            "Authorization": f"Bearer {self.__token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip"
        }