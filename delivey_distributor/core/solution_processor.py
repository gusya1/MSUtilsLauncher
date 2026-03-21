import datetime

from .data_structure import CourierData, OrderData
from .delivery_data_preparator import prepare_points


def seconds_to_time(seconds: int) -> datetime.time:
    """
    Преобразует количество секунд от начала дня в объект datetime.time.
    """
    seconds %= 86400  # опционально, чтобы корректно обрабатывать значения >= 86400
    midnight = datetime.datetime.combine(datetime.date.min, datetime.time.min)
    result_time = midnight + datetime.timedelta(seconds=seconds)
    return result_time.time()

def extract_solution(solution, manager, routing, orders, couriers):
    """
    Извлекает маршруты и времена прибытия.
    Возвращает список словарей с информацией о каждом курьере.
    """
    n_orders = len(orders)
    n_couriers = len(couriers)
    time_dimension = routing.GetDimensionOrDie('Time')
    
    results = []
    
    for vehicle_id in range(n_couriers):
        index = routing.Start(vehicle_id)
        route_nodes = []
        arrival_times = []
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            # Время прибытия в этот узел (в секундах от начала дня)
            time_var = time_dimension.CumulVar(index)
            arrival_time = solution.Value(time_var)
            
            if node < n_orders:
                # Это заказ
                route_nodes.append(node)
                arrival_times.append(arrival_time)
            # Если node >= n_orders, это стартовая или конечная точка, мы их пропускаем в основном списке, 
            # но можно добавить отдельно
            
            index = solution.Value(routing.NextVar(index))
        
        # Последний узел (конечная точка) тоже имеет время
        final_node = manager.IndexToNode(index)
        start_time = solution.Value(time_dimension.CumulVar(routing.Start(vehicle_id)))
        end_time = solution.Value(time_dimension.CumulVar(routing.End(vehicle_id)))
        
        results.append({
            'courier_id': vehicle_id,
            'courier_name': couriers[vehicle_id].name,
            'order_indices': route_nodes,
            'arrival_times_seconds': arrival_times,
            'start_time_seconds': start_time,
            'end_time_seconds': end_time,
            'span_time_seconds': end_time - start_time,
        })
    
    return results

def print_routes(results, orders):
    for res in results:
        print(f"\nКурьер: {res['courier_name']}")
        print(f"Начало маршрута: {res['start_time_seconds'] / 3600:.2f} часов")
        print(f"Конец маршрута: {res['end_time_seconds'] / 3600:.2f} часов")
        print(f"Общее время маршрута: {res['span_time_seconds'] / 3600:.2f} часов")
        print("Заказы (в порядке посещения):")
        for idx, order_node in enumerate(res['order_indices']):
            order = orders[order_node]
            arrival = res['arrival_times_seconds'][idx]
            arrival_time = seconds_to_time(arrival)
            window_start = order.start_time
            window_end = order.end_time
            print(f"  {idx+1}. {order.address}")
            print(f"     Время прибытия: {arrival_time.strftime('%H:%M')}")
            print(f"     Окно доставки: {window_start.strftime('%H:%M')} - {window_end.strftime('%H:%M')}")

def export_routes_to_geojson(results: list[dict], orders: list[OrderData], couriers: list[CourierData]) -> dict[str, object]:
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

    # Цвета для курьеров (можно сделать по выбору)
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFA500", "#800080", "#FFC0CB", "#00FFFF", "#FFD700"]

    # 1. Линии маршрутов
    for res in results:
        courier_id = res['courier_id']
        courier_name = res['courier_name']
        order_indices = res['order_indices']

        # Координаты линии: старт -> заказы -> финиш
        line_coords = []
        # Старт
        start_node = start_indices[courier_id]
        line_coords.append([all_points[start_node].longitude, all_points[start_node].latitude])
        # Заказы в порядке
        for order_idx in order_indices:
            line_coords.append([all_points[order_idx].longitude, all_points[order_idx].latitude])
        # Финиш
        end_node = end_indices[courier_id]
        line_coords.append([all_points[end_node].longitude, all_points[end_node].latitude])

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": line_coords
            },
            "properties": {
                "type": "route",
                "courier": courier_name,
                "stroke": colors[courier_id % len(colors)],
                "total_time_seconds": res['span_time_seconds']
            }
        })

    # 2. Точки заказов
    # Для быстрого доступа к времени прибытия по индексу заказа создадим словарь
    order_arrival = {}
    for res in results:
        for order_idx, arrival_sec in zip(res['order_indices'], res['arrival_times_seconds']):
            order_arrival[order_idx] = arrival_sec

    for order_idx, order in enumerate(orders):
        arrival_sec = order_arrival.get(order_idx)
        arrival_str = ""
        if arrival_sec is not None:
            arrival_time = seconds_to_time(arrival_sec)
            arrival_str = arrival_time.strftime("%H:%M")
        else:
            arrival_str = "не назначен"

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [order.longitude, order.latitude]
            },
            "properties": {
                "type": "order",
                "address": order.address,
                "time_window": f"{order.start_time.strftime('%H:%M')} - {order.end_time.strftime('%H:%M')}",
                "arrival_time": arrival_str,
                "color": "#888888"
            }
        })

    # 3. Точки старта
    for courier_id, courier in enumerate(couriers):
        point = all_points[start_indices[courier_id]]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [point.longitude, point.latitude]
            },
            "properties": {
                "type": "start",
                "courier": courier.name,
                "color": colors[courier_id % len(colors)],
                "marker-symbol": "warehouse"
            }
        })

    # 4. Точки финиша
    for courier_id, courier in enumerate(couriers):
        point = all_points[end_indices[courier_id]]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [point.longitude, point.latitude]
            },
            "properties": {
                "type": "end",
                "courier": courier.name,
                "color": colors[courier_id % len(colors)],
                "marker-symbol": "home"
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return geojson

