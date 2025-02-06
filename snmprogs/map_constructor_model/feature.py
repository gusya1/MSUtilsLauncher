import typing
import pydantic

from .geometry import Geometry
from .properties import Properties

Props = typing.TypeVar("Props", bound=typing.Union[typing.Dict[str, typing.Any], Properties])
Geom = typing.TypeVar("Geom", bound=Geometry)


class Feature(pydantic.BaseModel, typing.Generic[Geom, Props]):
    type: typing.Literal["Feature"] = "Feature"
    id: int
    geometry: Geom
    properties: Props
