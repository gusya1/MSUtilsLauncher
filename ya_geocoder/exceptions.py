
class YandexGeocoderError(Exception):
    pass

class ResponseError(YandexGeocoderError):
    pass

class InvalidKeyError(ResponseError):
    pass

class TooManyRequestsError(ResponseError):
    pass

class NothingFonudError(ResponseError):
    pass

class UnexpectedResponseError(YandexGeocoderError):
    pass
