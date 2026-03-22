import pydantic
import datetime


class Point(pydantic.BaseModel):
    longitude: float
    latitude: float

class OrderData(pydantic.BaseModel):
    name: str
    point: Point | None = None
    address: str
    start_time: datetime.time
    end_time: datetime.time
    weight: float

class CourierData(pydantic.BaseModel):
    end: Point | None = None
    start: Point
    capacitiy: int
    name: str = ""

