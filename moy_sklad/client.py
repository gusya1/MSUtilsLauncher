from requests import Session
from requests.adapters import HTTPAdapter, Retry

import urllib.parse


def _create_session():
    session = Session()
    session.mount('https://',
                  HTTPAdapter(max_retries=Retry(total=10, status_forcelist=[500, 503])))
    return session


def _make_url(request: str):
    ms_url = "https://api.moysklad.ru/api/remap/1.2"
    return f"{ms_url}/{request}"


class MsClient:

    def __init__(self):
        self.__token: str | None = None
        self.__session = _create_session()

    def set_token(self, token: str):
        self.__token = token

    def post(self, request, **kwargs):
        request = urllib.parse.quote(request)
        return self.__session.post(_make_url(request), headers=self.__make_auth_headers(), **kwargs)

    def get(self, request, **kwargs):
        urllib.parse.quote(request)
        return self.__session.get(_make_url(request), headers=self.__make_auth_headers(), **kwargs)

    def put(self, request, **kwargs):
        request = urllib.parse.quote(request)
        return self.__session.put(_make_url(request), headers=self.__make_auth_headers(), **kwargs)

    def __make_auth_headers(self):
        return {"Authorization": f"Bearer {self.__token}",
                "Content-Type": "application/json", "Accept-Encoding": "gzip"}
