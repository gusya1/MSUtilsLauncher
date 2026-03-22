from ortools.constraint_solver import routing_enums_pb2, pywrapcp

def add_time_dimension(routing, manager, data):
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        travel_time = data['time_matrix'][from_node][to_node]
        service_time = data['service_times'][from_node]
        traffic_factor = 0.3
        return int(travel_time * (1 + traffic_factor) + service_time)
    
    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    
    # Задаём стоимость как сумму времени всех переездов (минимизация общего времени)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Добавляем измерение времени (Time Windows)
    routing.AddDimension(
        transit_callback_index,
        data['max_waiting_time'],  # допустимое время ожидания
        data['max_time'],     # максимальное время маршрута
        False,  # не заставлять суммировать время от начала (start cumul to zero)
        'Time')
    time_dimension = routing.GetDimensionOrDie('Time')
    
    for node_idx, (window_start, window_end) in enumerate(data['time_windows']):
        if window_start is not None and window_end is not None:
            index = manager.NodeToIndex(node_idx)
            assert(index >= 0)
            time_dimension.CumulVar(index).SetRange(int(window_start), int(window_end))
    
    for vehicle_id in range(data['num_vehicles']):
        start_index = routing.Start(vehicle_id)
        end_index = routing.End(vehicle_id)

        start, end = data['work_time_interval']
        time_dimension.CumulVar(start_index).SetRange(start, end)
        time_dimension.CumulVar(end_index).SetRange(start, end)

        time_dimension.SetSpanUpperBoundForVehicle(data['work_hours'], vehicle_id)


def add_capacity_dimension(routing, manager, data):
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]
        
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # slack (здесь не нужен)
        data['vehicle_capacities'],
        True,  # start cumul = 0
        'Capacity')
    

def solve_vrp(data):
    manager = pywrapcp.RoutingIndexManager(
        len(data['time_matrix']), 
        data['num_vehicles'], 
        data['starts'], 
        data['ends'])
    routing = pywrapcp.RoutingModel(manager)
    
    add_time_dimension(routing, manager, data)
    add_capacity_dimension(routing, manager, data)

    # Настройки поиска решения
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 30  # лимит времени на поиск
    
    solution = routing.SolveWithParameters(search_parameters)
    return solution, manager, routing