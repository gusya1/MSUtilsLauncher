import requests
from requests.adapters import HTTPAdapter, Retry

from .exceptions import ResponseError, InvalidKeyError, TooManyRequestsError, NothingFonudError, UnexpectedResponseError


def _create_session():
    session = requests.Session()
    session.mount('https://',
                  HTTPAdapter(max_retries=Retry(total=10, status_forcelist=[500, 503])))
    return session

def _check_error(response):
    if response.status_code == 200:
        return

    if response.status_code == 403:
        raise InvalidKeyError(response.json()["message"])
    if response.status_code == 429:
        raise TooManyRequestsError(response.json()["message"])
    if response.status_code == 400:
        raise ResponseError(response.json()["message"])
    else:
        raise UnexpectedResponseError(
            f"status_code={response.status_code}"
        )


class Client:
    api_url = "https://geocode-maps.yandex.ru/1.x/"

    def __init__(self, token: str = None):
        self.__token = token
        self.__session = _create_session()

    def get_coordinates(self, address, **kwargs):
        data = self._get(self._make_address_request_params(address), **kwargs)
        if not data:
            raise NothingFonudError(f'Nothing found for "{address}" not found')

        coordinates: str = data["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
        longitude, latitude = tuple(coordinates.split(" "))
        return float(longitude), float(latitude)

    def _get(self, params: dict, **kwargs):
        response = requests.get(self.api_url, params=params, **kwargs)
        _check_error(response)
        return response.json()["response"]

    def _make_address_request_params(self, address):
        return dict(format="json", apikey=self.__token, geocode=address)
