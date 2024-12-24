
from MSApi import Project, CustomerOrder, Filter, MSApi, \
    error_handler, MSApiException, MSApiHttpException
import json

from moy_sklad_utils import filters, auth
from .palette_settings import get_projects_by_color

def find_project_by_name(project_name):
    for project in Project.gen_list():
        if project.get_name() != project_name:
            continue
        return project
    else:
        raise RuntimeError("Проект {} не найден".format(project_name))

def run(geojson_data, date):
    error_list = []
    change_list = []
    try:
        MSApi.set_access_token(auth.get_moy_sklad_token())

        orders = {}

        gmap = json.loads(geojson_data)
        for feature in gmap.get("features", []):
            try:
                props = feature["properties"]
                id = props["iconCaption"].split(" ")[0]
                color = props["marker-color"]
                orders[id] = color
            except KeyError as e:
                error_list.append("Объект {}: Поле {} не найдено".format(str(feature.get("id", "None")), str(e)))

        projects_by_color = get_projects_by_color()

        for order_id, color in orders.items():
            try:
                project: Project = find_project_by_name(projects_by_color.get(color, None))
                date_filter = filters.get_one_day_filter('deliveryPlannedMoment', date)
                if not project:
                    error_list.append("Заказ {}: Цвет {} не определён".format(order_id, color))
                    continue
                customer_orders = list(CustomerOrder.gen_list(filters= Filter.eq("name", order_id) + date_filter))
                if not customer_orders:
                    error_list.append("Заказ {}: Заказ не найден".format(order_id))
                    continue
                if len(customer_orders) > 1:
                    error_list.append("Заказ {}: Неоднозначный номер заказа".format(order_id))
                    continue

                order: CustomerOrder = customer_orders[0]
                order_proj = order.get_project()
                if order_proj is not None:
                    error_list.append("Заказ {}: Проект уже заполнен".format(order_id))
                    continue

                updated_data = {
                    "project": {
                        "meta": project.get_meta().get_json()
                    }
                }

                response = MSApi.auch_put("entity/{}/{}".format(CustomerOrder.get_typename(), order.get_id()),
                                          json=updated_data)
                error_handler(response)
                change_list.append("Заказ {}: Проект успешно изменён на {}".format(order_id, project.get_name()))

            except MSApiException as e:
                error_list.append("Заказ {}: Ошибка МойСклад: {}".format(order_id, str(e)))

    except MSApiHttpException as e:
        error_list.append("Ошибка МойСклад: {}".format(str(e)))
        return False, change_list, error_list
    except MSApiException as e:
        error_list.append("Внутрянняя ошибка: {}".format(str(e)))
        return False, change_list, error_list
    except FileNotFoundError as e:
        error_list.append("Внутрянняя ошибка: {}".format(str(e)))
        return False, change_list, error_list

    return True, change_list, error_list
