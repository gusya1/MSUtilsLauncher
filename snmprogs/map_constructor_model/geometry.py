import typing
import pydantic
import typing_extensions

class Point(pydantic.BaseModel):
    type: typing.Literal["Point"] = "Point"
    coordinates: typing.Tuple[float, float]


Geometry = typing_extensions.Annotated[
    typing.Union[
        Point,
        #...
    ],
    pydantic.Field(discriminator="type"),
]