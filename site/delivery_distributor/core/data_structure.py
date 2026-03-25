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
    weight: float # кг

class CourierData(pydantic.BaseModel):
    enable: bool = True
    end: Point | None = None
    start: Point
    capacitiy: float # кг
    name: str = ""
    project: str = ""
    color: str = "#000000"

class RoutingSettingsData(pydantic.BaseModel):
    traffic_factor: float = 0
    fuel_factor: float = 10 # расход топлива на 100 км
    start_service_time_sec: int # время на загрузку в начальной точке
    order_service_time_sec: int # время на каждый заказ
    max_waiting_time_sec: int # максимальное время ожидания курьера
    max_time_sec: int # максимальное время когда курьер должен прибыть в конечную точку
    start_work_time_sec: int # время начала работы курьера
    end_work_time_sec: int # время окончания работы курьера
    work_hours_sec: int # рабочие часы курьера
    max_late_sec: int # максимальное время опоздания
    vehicle_start_cost: int # цена использования транспортного средства
    late_penalty: int # штраф за опоздание
    slack_penalty: int # штраф за секунду простоя
    exceed_work_hours_penalty: int # штраф за превышение рабочих часов
    exceed_work_time_penalty: int # штраф за выход из рабочего времени
    exceed_capacity_penalty: int # штраф за превышение вместимости курьера
    max_process_time_sec: int # максимальное время обработки маршрутов

class RoutingData(pydantic.BaseModel):
    time_matrix: list[list[float]]
    distance_matrix: list[list[float]]
    demands: list[int] # вес заказа (в граммах)
    time_windows: list[tuple[int, int]]
    service_times: list[int]
    num_vehicles: int
    num_orders: int
    vehicle_capacities: list[int] # вместимость курьера (в граммах)
    starts: list[int]
    ends: list[int]