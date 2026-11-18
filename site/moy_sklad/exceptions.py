

class MoySkladError(Exception):
    pass

class MoySkladConnectionError(Exception):
    pass

class MoySkladRateLimitError(MoySkladError):

    """Лимит запросов МойСклада исчерпан после N повторов (HTTP 429)."""

    pass

class UnauthorizedRequestError(MoySkladError):
    pass