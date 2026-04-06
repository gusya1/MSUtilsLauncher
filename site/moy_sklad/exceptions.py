

class MoySkladError(Exception):
    pass

class MoySkladConnectionError(Exception):
    pass

class UnauthorizedRequestError(MoySkladError):
    pass