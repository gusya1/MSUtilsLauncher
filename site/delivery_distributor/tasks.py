from celery import shared_task

from .core.delivery_data_preparator import create_data_model
from .core.solver import solve_vrp
from .core.solution_processor import extract_solution

from .core.data_structure import RoutingTaskData

@shared_task
def solve_vrp_task(task_data_json):
    task_data = RoutingTaskData.model_validate_json(task_data_json)
    data = create_data_model(task_data.orders, task_data.couriers, task_data.settings)
    solution, manager, routing = solve_vrp(data, task_data.settings)
    if solution:
        results = extract_solution(solution, manager, routing)
        return results
    return []