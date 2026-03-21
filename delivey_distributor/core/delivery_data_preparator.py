import datetime

from .data_structure import CourierData, OrderData, Point
from .osrm_client import compute_time_matrix


def prepare_points(orders: list[OrderData], couriers: list[CourierData]) -> list[Point]:
    """
    Собирает все точки: сначала заказы, затем старты, затем финиши.
    """
    points = []
    for order in orders:
        points.append(Point(order.longitude, order.latitude))

    for courier in couriers:
        points.append(Point(courier.start.longitude, courier.start.latitude))

    for courier in couriers:
        points.append(Point(courier.end.longitude, courier.end.latitude))
    
    return points


def duration_from_day_start(time: datetime.time) -> int:
    """
    Вычисляет время в секундах от начала дня до заданного времени.
    """
    return int(time.hour * 3600 + time.minute * 60 + time.second)

def end_of_day() -> int:
    return duration_from_day_start(datetime.time.max)

def get_order_time_windows(orders: list[OrderData]) -> list[tuple[float, float]]:
    """
    Вычисляет временные окна для заказов.
    """
    return [(duration_from_day_start(order.start_time), duration_from_day_start(order.end_time)) for order in orders]

def get_order_demands(orders):
    return [int(order.weight) for order in orders]

def create_data_model(orders: list[OrderData], couriers: list[CourierData]):
    data = {}
    # Матрица времени (в секундах) между всеми точками.
    # Индексы: 0..(num_orders-1) - заказы,
    # потом идут начальные точки курьеров, потом конечные (или отдельно).
    # Удобно сделать так:
    # - Точки заказов: 0 .. n-1
    # - Старты курьеров: n .. n+num_vehicles-1
    # - Финиши курьеров: n+num_vehicles .. n+2*num_vehicles-1
    # Тогда для каждого курьера задаём start_index и end_index.
    points = prepare_points(orders, couriers)
    data['time_matrix'] = compute_time_matrix(points)
    n_orders = len(orders)
    n_couriers = len(couriers)

    data['demands'] = get_order_demands(orders) + ([0] * (2 * len(couriers)))

    # Временные окна для всех точек.
    # Для заказов: [ready_time, due_time].
    # (можно задать жёсткое окно или добавить штраф за опоздание).
    data['time_windows'] = get_order_time_windows(orders)
    
    data['service_times'] = ([60 * 10] * n_orders) + ([60 * 30] * n_couriers) + ([0] * n_couriers)
    
    # Количество курьеров
    data['num_vehicles'] = n_couriers
    data['num_orders'] = n_orders
    
    # вместимость курьеров
    data['vehicle_capacities'] = [courier.capacitiy for courier in couriers]
    
    # Индексы старта и финиша для каждого курьера
    data['starts'] = [n_orders + i for i in range(n_couriers)]
    data['ends'] = [n_orders + n_couriers + i for i in range(n_couriers)]

    # максимальное время ожидания курьера
    data['max_waiting_time'] = 24*3600
    # максимальное время когда курьер должен прибыть в конечную точку
    data['max_time'] = 24*3600
    # время работы курьеров
    data['work_time_interval'] = (0, end_of_day())
    # максимальные рабочие часы курьера
    data['work_hours'] = 8*3600

    return data