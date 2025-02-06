import pydantic

class Properties(pydantic.BaseModel):
    pass

class MapConstructorPointProperties(Properties):
    description: str
    iconCaption: str
    iconContent: str
    marker_color: str = pydantic.Field(alias='marker-color')