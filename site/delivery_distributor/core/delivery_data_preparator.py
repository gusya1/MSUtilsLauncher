import datetime
import logging
import json

from .data_structure import CourierData, OrderData, Point, RoutingData, RoutingSettingsData
from .osrm_client import compute_distance_matrix, compute_matrices, compute_time_matrix

logger = logging.getLogger("delivery_distributor")

def prepare_points(orders: list[OrderData], couriers: list[CourierData]) -> list[Point]:
    """
    Собирает все точки: сначала заказы, затем старты, затем финиши.
    """
    points = []
    for order in orders:
        points.append(order.point)

    for courier in couriers:
        points.append(courier.start)

    for courier in couriers:
        if courier.end:
            points.append(courier.end)
        else:
            points.append(Point(longitude=0, latitude=0))

    return points


def duration_from_day_start(time: datetime.time) -> int:
    """
    Вычисляет время в секундах от начала дня до заданного времени.
    """
    return int(time.hour * 3600 + time.minute * 60 + time.second)

def end_of_day() -> int:
    return duration_from_day_start(datetime.time.max)

def get_order_time_windows(orders: list[OrderData]) -> list[tuple[int, int]]:
    """
    Вычисляет временные окна для заказов.
    """
    return [(duration_from_day_start(order.start_time), duration_from_day_start(order.end_time)) for order in orders]

def get_order_demands(orders):
    return [int(order.weight * 1000) for order in orders]

def get_courier_capacities(couriers: list[CourierData]):
    return [int(courier.capacitiy * 1000) for courier in couriers]

def create_data_model(orders: list[OrderData], couriers: list[CourierData], settings: RoutingSettingsData):
    # Матрица времени (в секундах) между всеми точками.
    # Индексы: 0..(num_orders-1) - заказы,
    # потом идут начальные точки курьеров, потом конечные (или отдельно).
    # Удобно сделать так:
    # - Точки заказов: 0 .. n-1
    # - Старты курьеров: n .. n+num_vehicles-1
    # - Финиши курьеров: n+num_vehicles .. n+2*num_vehicles-1
    # Тогда для каждого курьера задаём start_index и end_index.
    points = prepare_points(orders, couriers)
    time_matrix, distance_matrix = compute_matrices(points)


    n_orders = len(orders)
    n_couriers = len(couriers)
    
    demands = get_order_demands(orders) + ([0] * (2 * n_couriers))

    # Временные окна для заказов.
    # Для заказов: [ready_time, due_time].
    time_windows = get_order_time_windows(orders)
    
    # Время обслуживания заказов.
    service_times = ([settings.order_service_time_sec] * n_orders) + ([settings.start_service_time_sec] * n_couriers) + ([0] * n_couriers)

    
    # вместимость курьеров
    vehicle_capacities = get_courier_capacities(couriers)
    
    # Индексы старта и финиша для каждого курьера
    starts = [n_orders + i for i in range(n_couriers)]
    ends = [n_orders + n_couriers + i for i in range(n_couriers)]

    # зануляем время до финиша ля курьеров без дома
    for i, courier in enumerate(couriers):
        if not courier.end:
            end_index = ends[i]
            time_matrix[end_index] = [0] * len(time_matrix)
            for line in time_matrix:
                line[end_index] = 0

    return RoutingData(
        time_matrix=time_matrix,
        distance_matrix=distance_matrix,
        demands=demands,
        time_windows=time_windows,
        service_times=service_times,
        num_vehicles=n_couriers,
        num_orders=n_orders,
        vehicle_capacities=vehicle_capacities,
        starts=starts,
        ends=ends,
    )