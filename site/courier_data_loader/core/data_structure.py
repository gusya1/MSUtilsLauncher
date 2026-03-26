from pydantic import BaseModel


class OrderCourierData(BaseModel):
    order_name: str
    project: str
    delivery_order_number: int

class OrdersCourierData(BaseModel):
    orders: list[OrderCourierData]

class ResultData(BaseModel):
    change_list: list[str]
    error_list: list[str] 
    status: str