from celery import shared_task

from .core.delivery_data_preparator import create_data_model
from .core.solver import solve_vrp
from .core.solution_processor import extract_solution

from .core.data_structure import RoutingData, RoutingSettingsData

# @shared_task(bind=True)
# def solve_vrp_task(self, data_json, settings_data_json):
#     data = RoutingData.model_validate_json(data_json)
#     settings_data = RoutingSettingsData.model_validate_json(settings_data_json)
#     solution, manager, routing = solve_vrp(data, settings_data)
#     if solution:
#         results = extract_solution(solution, manager, routing, orders_data, couriers_data)
#         return results
#     return []