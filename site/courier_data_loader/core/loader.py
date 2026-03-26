

from dataclasses import dataclass
import uuid

from pydantic import BaseModel

from moy_sklad.client import MoySkladClient
from moy_sklad import getters, model, updaters
from moy_sklad.exceptions import MoySkladError
from moy_sklad.utils import make_entity_meta_filed
from moy_sklad_settings.models import MoySkladSettings
from moy_sklad_settings.utils import get_moy_sklad_token

from .data_structure import OrderCourierData, OrdersCourierData, ResultData


def find_customer_order_attribute_by_name(client: MoySkladClient, attribute_name):
    attributes = list(attr for attr in getters.get_attibutes_for_entity(client, model.MoySkladCustomerOrder) if attr.name == attribute_name)
    if len(attributes) > 1:
        raise RuntimeError("Неоднозначное имя аттрибута: {}".format(attribute_name))
    if len(attributes) < 1:
        raise RuntimeError("Аттрибут '{}' не найден".format(attribute_name))
    return attributes[0]


def find_project_by_name(client: MoySkladClient, project_name):
    projects = list(getters.walk_for_all(client, model.MoySkladProject, filter=f"name={project_name}"))
    if len(projects) > 1:
        raise RuntimeError("Неоднозначное имя проекта: {}".format(project_name))
    if len(projects) < 1:
        raise RuntimeError("Проект '{}' не найден".format(project_name))
    return projects[0]

def find_customer_order_by_name(client: MoySkladClient, order_name):
    orders = list(getters.walk_for_all(client, model.MoySkladCustomerOrder, filter=f"name={order_name}"))
    if len(orders) > 1:
        raise RuntimeError("Неоднозначное имя заказа: {}".format(order_name))
    if len(orders) < 1:
        raise RuntimeError("Заказ '{}' не найден".format(order_name))
    return orders[0]


def get_customer_order(client: MoySkladClient, order_id: uuid.UUID):
    return getters.get_entity_by_id(client, model.MoySkladCustomerOrder, order_id)

def check_customer_order_project(customer_order: model.MoySkladCustomerOrder):
    if customer_order.project is not None:
        raise RuntimeError("Проект уже заполнен")

def update_customer_order(client: MoySkladClient, order_id, updated_data: model.MoySkladCustomerOrderBase):
    try:
        updaters.update_entity(client, order_id, updated_data)
    except MoySkladError as e:
        raise RuntimeError("Ошибка заполнения заказа: {}".format(str(e)))
    


def process_courier_data(client: MoySkladClient, 
                         delivery_order_attribute: model.MoySkladAttributeInfo, 
                         data: OrderCourierData):
    project: model.MoySkladProject = find_project_by_name(client, data.project)
    customer_order: model.MoySkladCustomerOrder = find_customer_order_by_name(client, data.order_name)
    check_customer_order_project(customer_order)

    updated_data = model.MoySkladCustomerOrderUpdate(
        project=make_entity_meta_filed(project),
        attributes=[
            model.MoySkladAttributeCreate(
                meta=delivery_order_attribute.meta,
                value=data.delivery_order_number
            )
        ]
    )

    update_customer_order(client, customer_order.id, updated_data)

# throws: RuntimeError
def load_courier_data(orders_courier_data: OrdersCourierData) -> ResultData:
    client = MoySkladClient(get_moy_sklad_token())

    change_list = []
    error_list = []
    status = "Обработка заказов завершена"

    try:
        delivery_order_attribute_name = MoySkladSettings.get_solo().delivery_order_attribute_name
        delivery_order_attribute: model.MoySkladAttributeInfo = find_customer_order_attribute_by_name(client, delivery_order_attribute_name)



        for data in orders_courier_data.orders:
            try:
                process_courier_data(client, delivery_order_attribute, data)
                change_list.append("Заказ {} обработан. Проект: '{}', {}: '{}'".format(data.order_name, data.project, delivery_order_attribute_name, data.delivery_order_number))
            except RuntimeError as e:
                error_list.append("Ошибка обработки заказа {}: {}".format(data.order_name, str(e)))
    except (MoySkladError, RuntimeError) as e:
        status = "Ошибка обработки заказов: {}".format(str(e))

    return ResultData(change_list=change_list, error_list=error_list, status=status)