from celery import shared_task

from .run.main import accounts_synchronize
from .core.data_structure import TaskData, ResultData

@shared_task
def accounts_synchronize_task(task_data_json):
    task_data = TaskData.model_validate_json(task_data_json)
    status, output = accounts_synchronize(task_data.date)
    if status:
        return ResultData(change_list=output).model_dump_json()
    else:
        return ResultData(error=output).model_dump_json()