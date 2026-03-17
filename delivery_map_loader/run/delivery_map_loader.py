from MSApi import Project, CustomerOrder, MSApi, \
    error_handler, MSApiException, MSApiHttpException

from moy_sklad_utils import filters, auth
from MSApi import Filter

from . import settings
from map_constructor_model.feature_collection import FeatureCollection
from map_constructor_model.feature import Feature
from map_constructor_model.properties import MapConstructorPointProperties


def update_customer_order(order_id, updated_data):
    try:
        response = MSApi.auch_put("entity/{}/{}".format(CustomerOrder.get_typename(), order_id), json=updated_data)
        error_handler(response)
    except MSApiException as e:
        raise RuntimeError("Заказ {}: Ошибка МойСклад: {}".format(order_id, str(e)))


def find_project_by_name(project_name):
    projects = list(Project.gen_list(filters=Filter.eq("name", project_name)))
    if len(projects) > 1:
        raise RuntimeError("Неоднозначное имя проекта: {}".format(project_name))
    if len(projects) < 1:
        raise RuntimeError("Проект '{}' не найден".format(project_name))
    return projects[0]


def find_customer_order_by_name(order_id, additional_filters=None):
    name_filter = Filter.eq("name", order_id)
    customer_order_filters = name_filter + additional_filters if additional_filters else name_filter
    customer_orders = list(CustomerOrder.gen_list(filters=customer_order_filters))
    if len(customer_orders) > 1:
        raise RuntimeError("Неоднозначный номер заказа: {}".format(order_id))
    if len(customer_orders) < 1:
        raise RuntimeError("Заказ '{}' не найден".format(order_id))
    return customer_orders[0]


def find_customer_order_attribute_by_name(attribute_name):
    attributes = list(filter(lambda attr: attr.get_name() == attribute_name, CustomerOrder.gen_attributes_list()))
    if len(attributes) > 1:
        raise RuntimeError("Неоднозначное имя аттрибута: {}".format(attribute_name))
    if len(attributes) < 1:
        raise RuntimeError("Аттрибут '{}' не найден".format(attribute_name))
    return attributes[0]


def check_customer_order_project(customer_order: CustomerOrder):
    if customer_order.get_project() is not None:
        raise RuntimeError("Заказ {}: Проект уже заполнен".format(customer_order.get_name()))


def get_project_by_color(projects_by_color, color) -> Project:
    project_name = projects_by_color.get(color, None)
    if project_name is None:
        raise RuntimeError("Цвет {} не определён".format(color))
    return find_project_by_name(project_name)


def get_properties(feature: Feature) -> MapConstructorPointProperties:
    return MapConstructorPointProperties.model_validate(feature.properties)


def get_order_id_from_icon_caption(icon_caption: str) -> str:
    return icon_caption.split(" ")[0]


def run(geojson_data, date):
    error_list = []
    change_list = []
    try:
        MSApi.set_access_token(auth.get_moy_sklad_token())

        settings_model = settings.read_palette()
        projects_by_color = settings_model.palette
        delivery_order_attribute_name = settings_model.delivery_order_attribute_name

        date_filter = filters.get_one_day_filter('deliveryPlannedMoment', date)
        delivery_order_attribute = find_customer_order_attribute_by_name(delivery_order_attribute_name)

        collection = FeatureCollection.model_validate_json(geojson_data)
        for feature in collection.features:
            try:
                properties = get_properties(feature)
                order_id = get_order_id_from_icon_caption(properties.iconCaption)
                project = get_project_by_color(projects_by_color, properties.marker_color)
                delivery_order_number = int(properties.iconContent)
                customer_order = find_customer_order_by_name(order_id, date_filter)

                check_customer_order_project(customer_order)

                updated_data = {
                    "project": {
                        "meta": project.get_meta().get_json()
                    },
                    "attributes": [
                        {
                            "meta": delivery_order_attribute.get_meta().get_json(),
                            "value": delivery_order_number
                        }
                    ]
                }

                update_customer_order(customer_order.get_id(), updated_data)
                change_list.append("Заказ {}: проект - '{}', {} - {}".format(order_id, project.get_name(),
                                                                             delivery_order_attribute_name,
                                                                             delivery_order_number))
            except RuntimeError as e:
                error_list.append(str(e))

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
