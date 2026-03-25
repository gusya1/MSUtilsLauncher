import datetime
import logging

from .data_structure import CourierData, OrderData
from .delivery_data_preparator import prepare_points

logger = logging.getLogger("delivery_distributor")

def seconds_to_time(seconds: int) -> datetime.time:
    """
    Преобразует количество секунд от начала дня в объект datetime.time.
    """
    seconds %= 86400  # опционально, чтобы корректно обрабатывать значения >= 86400
    midnight = datetime.datetime.combine(datetime.date.min, datetime.time.min)
    result_time = midnight + datetime.timedelta(seconds=seconds)
    return result_time.time()


def extract_solution(solution, manager, routing, orders, couriers):

    n_orders = len(orders)
    n_couriers = len(couriers)
    time_dimension = routing.GetDimensionOrDie("Time")
    fuel_dimension = routing.GetDimensionOrDie("Fuel")
    capacity_dimension = routing.GetDimensionOrDie("Capacity")

    results = []

    for vehicle_id in range(n_couriers):

        index = routing.Start(vehicle_id)

        route_nodes = []
        arrival_times = []
        total_waiting_time = 0

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            arrival_time = solution.Value(time_dimension.CumulVar(index))
            waiting_time = solution.Value(time_dimension.SlackVar(index))
            total_waiting_time += waiting_time

            if node < n_orders:
                route_nodes.append(node)
                arrival_times.append(arrival_time)

            index = solution.Value(routing.NextVar(index))

        start_time = solution.Value(time_dimension.CumulVar(routing.Start(vehicle_id)))
        end_time = solution.Value(time_dimension.CumulVar(routing.End(vehicle_id)))
        
        fuel_cost = solution.Value(fuel_dimension.CumulVar(routing.End(vehicle_id)))
        capacity = solution.Value(capacity_dimension.CumulVar(routing.End(vehicle_id)))

        if not route_nodes:
            continue

        results.append(
            {
                "courier_id": vehicle_id,
                "courier_name": couriers[vehicle_id].name,
                "order_indices": route_nodes,
                "arrival_times_seconds": arrival_times,
                "start_time_seconds": start_time,
                "end_time_seconds": end_time,
                "span_time_seconds": end_time - start_time,
                "waiting_time_seconds": total_waiting_time,
                "fuel_cost": fuel_cost,
                "capacity": capacity / 1000,
            }
        )

    return results


def print_routes(results, orders):
    for res in results:
        print(f"\nКурьер: {res['courier_name']}")
        print(f"Начало маршрута: {res['start_time_seconds'] / 3600:.2f} часов")
        print(f"Конец маршрута: {res['end_time_seconds'] / 3600:.2f} часов")
        print(f"Общее время маршрута: {res['span_time_seconds'] / 3600:.2f} часов")
        print("Заказы (в порядке посещения):")
        for idx, order_node in enumerate(res["order_indices"]):
            order = orders[order_node]
            arrival = res["arrival_times_seconds"][idx]
            arrival_time = seconds_to_time(arrival)
            window_start = order.start_time
            window_end = order.end_time
            print(f"  {idx+1}. {order.address}")
            print(f"     Время прибытия: {arrival_time.strftime('%H:%M')}")
            print(
                f"     Окно доставки: {window_start.strftime('%H:%M')} - {window_end.strftime('%H:%M')}"
            )


def make_context(results, orders):
    context = {}
    context["couriers"] = []
    for res in results:
        courier = {
            "name": res["courier_name"],
            "start_time": datetime.timedelta(seconds=res["start_time_seconds"]),
            "end_time": datetime.timedelta(seconds=res["end_time_seconds"]),
            "span_time": datetime.timedelta(seconds=res["span_time_seconds"]),
            "waiting_time": datetime.timedelta(seconds=res["waiting_time_seconds"]),
            "fuel_cost": res["fuel_cost"],
            "capacity": res["capacity"],
        }
        courier["orders"] = []
        for idx, order_node in enumerate(res["order_indices"]):
            order = orders[order_node]
            arrival = res["arrival_times_seconds"][idx]
            arrival_time = seconds_to_time(arrival)
            window_start = order.start_time
            window_end = order.end_time
            courier["orders"].append(
                {
                    "address": order.address,
                    "arrival_time": arrival_time,
                    "window_start": window_start,
                    "window_end": window_end,
                }
            )
        context["couriers"].append(courier)
    return context


colors = ["#FF0000", "#00FF00", "#0000FF", "#800080", "#FFC0CB", "#00FFFF"]


def export_routes_lines_to_geojson(
    results: list[dict], orders: list[OrderData], couriers: list[CourierData]
) -> dict[str, object]:
    """
    Преобразует маршруты в GeoJSON FeatureCollection.
    Возвращает словарь, который можно сохранить как JSON.
    """
    # Соберём все точки для доступа по индексам
    all_points = prepare_points(orders, couriers)
    n_orders = len(orders)
    n_couriers = len(couriers)
    start_indices = [n_orders + i for i in range(n_couriers)]
    end_indices = [n_orders + n_couriers + i for i in range(n_couriers)]

    features = []

    # 1. Линии маршрутов
    for res in results:
        courier_id = res["courier_id"]
        order_indices = res["order_indices"]

        # Координаты линии: старт -> заказы -> финиш
        line_coords = []
        # Старт
        start_node = start_indices[courier_id]
        line_coords.append(
            [all_points[start_node].longitude, all_points[start_node].latitude]
        )
        # Заказы в порядке
        for order_idx in order_indices:
            line_coords.append(
                [all_points[order_idx].longitude, all_points[order_idx].latitude]
            )
        # Финиш
        end_node = end_indices[courier_id]
        if all_points[end_node].longitude != 0 and all_points[end_node].latitude != 0:
            line_coords.append(
                [all_points[end_node].longitude, all_points[end_node].latitude]
            )

        features.append(
            {
                "id": len(features),
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": line_coords},
                "style": {
                    "stroke": [{"width": 2, "color": colors[courier_id % len(colors)]}],
                },
                "properties": {
                    "type": "route",
                },
            }
        )

    geojson = {"type": "FeatureCollection", "features": features}
    return geojson


def get_marker_html(content, color) -> str:
    marker_size = 20
    font_size = 12
    return f"""
    <div style="position: relative;">
    <div style="
        background: white; 
        width: {marker_size}px; 
        height: {marker_size}px; 
        border-radius: 50%; 
        border: 3px solid {color};
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        cursor: pointer;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: {font_size}px;
        text-align: center;
        line-height: {font_size}px;
    ">{content}</div>
    </div>
    """


def export_route_points(results: list[dict], orders: list[OrderData]):
    points = []

    # 2. Точки заказов
    # Для быстрого доступа к времени прибытия по индексу заказа создадим словарь

    order_infos = {}
    for res in results:
        for i, order_idx, arrival_sec in zip(
            range(len(res["order_indices"])),
            res["order_indices"],
            res["arrival_times_seconds"],
        ):
            order_infos[order_idx] = {
                "arrival_sec": arrival_sec,
                "number": i + 1,
                "courier_id": res["courier_id"],
            }

    for order_idx, order in enumerate(orders):
        order_info = order_infos.get(order_idx)

        points.append(
            {
                "id": order.name,
                "coordinates": [order.point.longitude, order.point.latitude],
                "html": get_marker_html(
                    order_info["number"], colors[order_info["courier_id"] % len(colors)]
                ),
            }
        )

    return points


def export_courier_break_points(results: list[dict], couriers: list[CourierData]):
    points = []
    for res in results:
        courier = couriers[res["courier_id"]]
        points.append({
            "id": "start_point_{}".format(courier.name),
            "coordinates": [courier.start.longitude, courier.start.latitude],
            "html": get_marker_html("S", colors[res["courier_id"] % len(colors)]),
        })
        if courier.end:
            points.append({
                "id": "end_point_{}".format(courier.name),
                "coordinates": [courier.end.longitude, courier.end.latitude],
                "html": get_marker_html("F", colors[res["courier_id"] % len(colors)]),
            })
    return points
