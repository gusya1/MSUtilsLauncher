import pydantic
import datetime


class TaskData(pydantic.BaseModel):
    start_date: datetime.date
    end_date: datetime.date
    order_state: str

class ResultData(pydantic.BaseModel):
    created_paymentsin: list[str] = []
    error: str | None = None