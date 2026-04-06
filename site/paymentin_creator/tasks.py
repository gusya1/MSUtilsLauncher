import time

from celery import shared_task

from .core.paymentin_creator import create_paymentin_for_customer_orders
from .core.data_structure import TaskData
from .models import PaymentInCreatorSettings

@shared_task
def create_paymentin_task(task_data_json):
    paymentin_state = PaymentInCreatorSettings.get_solo().paymentin_state
    task_data = TaskData.model_validate_json(task_data_json)
    result_data = create_paymentin_for_customer_orders(task_data, paymentin_state)
    return result_data.model_dump_json()