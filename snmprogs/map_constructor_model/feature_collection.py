import typing
import pydantic

from .feature import Feature


class FeatureCollectionMeta(pydantic.BaseModel):
    name: str


class FeatureCollection(pydantic.BaseModel):
    type: typing.Literal["FeatureCollection"] = "FeatureCollection"
    metadata: FeatureCollectionMeta
    features: typing.List[Feature]