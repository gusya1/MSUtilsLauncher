from datetime import datetime

from MSApi import Project, CustomerOrder, Filter, MSApi, \
    error_handler, MSApiException, MSApiHttpException, DateTimeFilter
import json
from .settings import MOY_SKLAD
from .palette import get_projects_by_color


def run(geojson_data):
    error_list = []
    change_list = []
    try:
        MSApi.set_access_token(MOY_SKLAD.TOKEN)

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

        current_year = datetime(datetime.now().year, 1, 1)
        for id, color in orders.items():
            try:
                project: Project = projects_by_color.get(color, None)
                if not project:
                    error_list.append("Заказ {}: Цвет {} не определён".format(id, color))
                    continue
                c_orders = list(CustomerOrder.gen_list(filters=
                                                       Filter.eq("name", id)
                                                       + DateTimeFilter.gt("deliveryPlannedMoment", current_year)))
                if not c_orders:
                    error_list.append("Заказ {}: Заказ не найден".format(id))
                    continue
                if len(c_orders) > 1:
                    error_list.append("Заказ {}: Неоднозначный номер заказа".format(id))
                    continue

                order: CustomerOrder = c_orders[0]
                order_proj = order.get_project()
                if order_proj is not None:
                    error_list.append("Заказ {}: Проект уже заполнен".format(id))
                    continue

                updated_data = {
                    "project": {
                        "meta": project.get_meta().get_json()
                    }
                }

                response = MSApi.auch_put("entity/{}/{}".format(CustomerOrder.get_typename(), order.get_id()),
                                          json=updated_data)
                error_handler(response)
                change_list.append("Заказ {}: Проект успешно изменён на {}".format(id, project.get_name()))

            except MSApiException as e:
                error_list.append("Заказ {}: Ошибка МойСклад: {}".format(id, str(e)))

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
