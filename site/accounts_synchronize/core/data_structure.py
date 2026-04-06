import pydantic
import datetime


class TaskData(pydantic.BaseModel):
    date: datetime.date
    
class ResultData(pydantic.BaseModel):
    change_list: list[str] = []
    error: str | None = None