import logging
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

logger = logging.getLogger("delivey_distributor")

def add_time_dimension(routing, manager, data):
    logger.debug("add_time_dimension")
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

    for index in range(routing.Size()):
        routing.AddToAssignment(time_dimension.SlackVar(index))

    # штраф за секунду простоя
    time_dimension.SetSlackCostCoefficientForAllVehicles(100)

    for node_idx, (window_start, window_end) in enumerate(data['time_windows']):
        if window_start is not None and window_end is not None:
            index = manager.NodeToIndex(node_idx)
            assert(index >= 0)
            max_late = 60*60
            time_dimension.CumulVar(index).SetRange(int(window_start) - max_late, int(window_end) + max_late)
            time_dimension.SetCumulVarSoftUpperBound(index, int(window_end), 1000) # штраф за опаздание
            time_dimension.SetCumulVarSoftLowerBound(index, int(window_start), 1000)  # штраф за ранний приезд

    for vehicle_id in range(data['num_vehicles']):
        start_index = routing.Start(vehicle_id)
        end_index = routing.End(vehicle_id)

        start, end = data['work_time_interval']
        time_dimension.CumulVar(start_index).SetRange(start, end)
        time_dimension.CumulVar(end_index).SetRange(start, end)

        bound_cost = pywrapcp.BoundCost(data['work_hours'], 10)
        time_dimension.SetSoftSpanUpperBoundForVehicle(bound_cost, vehicle_id)
        time_dimension.SetCumulVarSoftUpperBound(end_index, end, 100)
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(end_index))


def add_capacity_dimension(routing, manager, data):
    logger.debug("add_capacity_dimension")
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
    logger.debug("solve_vrp")
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
    search_parameters.time_limit.seconds = 60*1 # лимит времени на поиск
    # search_parameters.log_search = True

    logger.debug("SolveWithParameters")
    solution = routing.SolveWithParameters(search_parameters)
    return solution, manager, routing