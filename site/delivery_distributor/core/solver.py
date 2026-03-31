import logging
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

from .data_structure import RoutingData, RoutingSettingsData

logger = logging.getLogger("delivery_distributor")

def add_time_dimension(routing, manager, data: RoutingData, settings: RoutingSettingsData):
    logger.debug("add_time_dimension")
    
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        travel_time = data.time_matrix[from_node][to_node]
        service_time = data.service_times[from_node]
        return int(travel_time * (1 + settings.traffic_factor) + service_time)
    
    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Добавляем измерение времени (Time Windows)
    routing.AddDimension(
        transit_callback_index,
        settings.max_waiting_time_sec,  
        settings.max_time_sec,
        False,  # не заставлять суммировать время от начала (start cumul to zero)
        'Time')
    
    time_dimension = routing.GetDimensionOrDie('Time')

    for index in range(routing.Size()):
        routing.AddToAssignment(time_dimension.SlackVar(index))

    # штраф за секунду простоя
    time_dimension.SetSlackCostCoefficientForAllVehicles(settings.slack_penalty)

    for node_idx, (window_start, window_end) in enumerate(data.time_windows):
        if window_start is not None and window_end is not None:
            index = manager.NodeToIndex(node_idx)
            assert(index >= 0)
            time_dimension.CumulVar(index).SetRange(window_start - settings.max_late_sec, window_end + settings.max_late_sec)
            time_dimension.SetCumulVarSoftUpperBound(index, window_end, settings.late_penalty) # штраф за опаздание
            time_dimension.SetCumulVarSoftLowerBound(index, window_start, settings.late_penalty)  # штраф за ранний приезд

    for vehicle_id in range(data.num_vehicles):
        start_index = routing.Start(vehicle_id)
        end_index = routing.End(vehicle_id)

        start, end = settings.start_work_time_sec, settings.end_work_time_sec

        bound_cost = pywrapcp.BoundCost(settings.work_hours_sec, settings.exceed_work_hours_penalty)
        time_dimension.SetSoftSpanUpperBoundForVehicle(bound_cost, vehicle_id)
        time_dimension.SetCumulVarSoftUpperBound(end_index, end, settings.exceed_work_time_penalty)
        time_dimension.SetCumulVarSoftLowerBound(end_index, start, settings.exceed_work_time_penalty)
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(end_index))


def add_fuel_dimension(routing, manager, data: RoutingData, settings: RoutingSettingsData):
    
    def fuel_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        
        travel_distance = data.distance_matrix[from_node][to_node]
        fuel_cost = travel_distance * settings.fuel_factor / 100
        return int(fuel_cost)
    
    transit_callback_index = routing.RegisterTransitCallback(fuel_callback)
    
    # Добавляем измерение времени (Time Windows)
    routing.AddDimension(
        transit_callback_index,
        0,   
        100000000000,
        True,
        'Fuel')
    
    fuel_dimension = routing.GetDimensionOrDie('Fuel')

    fuel_dimension.SetSpanCostCoefficientForAllVehicles(settings.fuel_penalty)
    

def add_capacity_dimension(routing, manager, data: RoutingData, settings: RoutingSettingsData):
    logger.debug("add_capacity_dimension")
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data.demands[from_node]
        
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # slack (здесь не нужен)
        data.vehicle_capacities,
        True,  # start cumul = 0
        'Capacity')
    
    capacity_dimension = routing.GetDimensionOrDie('Capacity')
    for vehicle_id in range(data.num_vehicles):
        end_index = routing.End(vehicle_id)

        capacity_dimension.SetCumulVarSoftUpperBound(
            end_index,
            data.vehicle_capacities[vehicle_id],
            settings.exceed_capacity_penalty
        )
    
def add_order_dimension(routing, manager, data: RoutingData, settings: RoutingSettingsData):
        def order_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            if from_node >= data.num_orders:
                return 0
            return 1

        callback_index = routing.RegisterTransitCallback(order_callback)

        routing.AddDimension(
            callback_index,
            0,
            data.num_orders,
            True,
            "Orders"
        )

        orders_dimension = routing.GetDimensionOrDie("Orders")
        orders_dimension.SetGlobalSpanCostCoefficient(
            settings.balance_penalty
        )

def set_vehicle_restrictions(routing, manager, data: RoutingData, settings: RoutingSettingsData):
    for vehicle_id in range(data.num_vehicles):
        routing.SetFixedCostOfVehicle(settings.vehicle_start_cost, vehicle_id)

def solve_vrp(data: RoutingData, settings: RoutingSettingsData):
    logger.debug("solve_vrp")
    manager = pywrapcp.RoutingIndexManager(
        len(data.time_matrix), 
        data.num_vehicles, 
        data.starts, 
        data.ends)
    routing = pywrapcp.RoutingModel(manager)
    
    
    set_vehicle_restrictions(routing, manager, data, settings)
    add_time_dimension(routing, manager, data, settings)
    add_fuel_dimension(routing, manager, data, settings)
    add_capacity_dimension(routing, manager, data, settings)
    add_order_dimension(routing, manager, data, settings)

    # Настройки поиска решения
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = settings.max_process_time_sec # лимит времени на поиск
    search_parameters.log_search = True

    solution = routing.SolveWithParameters(search_parameters)
    return solution, manager, routing