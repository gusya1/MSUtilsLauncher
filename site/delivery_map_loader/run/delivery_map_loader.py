from datetime import timedelta

from moy_sklad.client import MoySkladClient
from moy_sklad import getters, model, updaters
from moy_sklad.exceptions import MoySkladError
from moy_sklad.utils import format_moy_sklad_datetime, make_entity_meta_filed
from moy_sklad_settings.models import MoySkladSettings
from moy_sklad_settings.utils import get_moy_sklad_token

from map_constructor_model.feature_collection import FeatureCollection
from map_constructor_model.feature import Feature
from map_constructor_model.properties import MapConstructorPointProperties

from delivery_map_loader.models import DeliveryMapPaletteSettings


def _get_one_day_filter(parameter, date):
    next_date = date + timedelta(days=1)
    return "{}>={};{}<{}".format(parameter, format_moy_sklad_datetime(date), parameter,
                                 format_moy_sklad_datetime(next_date))


def update_customer_order(client: MoySkladClient, customer_order: model.MoySkladCustomerOrder, updated_data):
    try:
        updaters.update_entity(client, customer_order.id, updated_data)
    except MoySkladError as e:
        raise RuntimeError("Заказ {}: Ошибка МойСклад: {}".format(customer_order.name, str(e)))


def find_project_by_name(client: MoySkladClient, project_name):
    projects = list(getters.walk_for_all(client, model.MoySkladProject, filter="name={}".format(project_name)))
    if len(projects) > 1:
        raise RuntimeError("Неоднозначное имя проекта: {}".format(project_name))
    if len(projects) < 1:
        raise RuntimeError("Проект '{}' не найден".format(project_name))
    return projects[0]


def find_customer_order_by_name(client: MoySkladClient, order_id, date_filter):
    customer_orders = list(getters.walk_for_all(
        client, model.MoySkladCustomerOrder, filter="name={};{}".format(order_id, date_filter)))
    if len(customer_orders) > 1:
        raise RuntimeError("Неоднозначный номер заказа: {}".format(order_id))
    if len(customer_orders) < 1:
        raise RuntimeError("Заказ '{}' не найден".format(order_id))
    return customer_orders[0]


def find_customer_order_attribute_by_name(client: MoySkladClient, attribute_name):
    attributes = [
        attr for attr in getters.get_attibutes_for_entity(client, model.MoySkladCustomerOrder)
        if attr.name == attribute_name
    ]
    if len(attributes) > 1:
        raise RuntimeError("Неоднозначное имя аттрибута: {}".format(attribute_name))
    if len(attributes) < 1:
        raise RuntimeError("Аттрибут '{}' не найден".format(attribute_name))
    return attributes[0]


def check_customer_order_project(customer_order: model.MoySkladCustomerOrder):
    if customer_order.project is not None:
        raise RuntimeError("Заказ {}: Проект уже заполнен".format(customer_order.name))


def get_project_by_color(client, projects_by_color, color) -> model.MoySkladProject:
    project_name = projects_by_color.get(color, None)
    if project_name is None:
        raise RuntimeError("Цвет {} не определён".format(color))
    return find_project_by_name(client, project_name)


def get_properties(feature: Feature) -> MapConstructorPointProperties:
    return MapConstructorPointProperties.model_validate(feature.properties)


def get_order_id_from_icon_caption(icon_caption: str) -> str:
    return icon_caption.split(" ")[0]


def run(geojson_data, date):
    error_list = []
    change_list = []
    try:
        client = MoySkladClient(get_moy_sklad_token())

        settings_model = DeliveryMapPaletteSettings.get_solo()
        projects_by_color = {item.color: item.project for item in settings_model.project_by_color.all()}
        ms_settings = MoySkladSettings.get_solo()
        delivery_order_attribute_name = ms_settings.delivery_order_attribute_name

        date_filter = _get_one_day_filter('deliveryPlannedMoment', date)
        delivery_order_attribute = find_customer_order_attribute_by_name(client, delivery_order_attribute_name)

        collection = FeatureCollection.model_validate_json(geojson_data)
        for feature in collection.features:
            try:
                properties = get_properties(feature)
                order_id = get_order_id_from_icon_caption(properties.iconCaption)
                project = get_project_by_color(client, projects_by_color, properties.marker_color)
                delivery_order_number = int(properties.iconContent)
                customer_order = find_customer_order_by_name(client, order_id, date_filter)

                check_customer_order_project(customer_order)

                updated_data = model.MoySkladCustomerOrderUpdate(
                    project=make_entity_meta_filed(project),
                    attributes=[
                        model.MoySkladAttributeCreate(meta=delivery_order_attribute.meta, value=delivery_order_number)
                    ],
                )

                update_customer_order(client, customer_order, updated_data)
                change_list.append("Заказ {}: проект - '{}', {} - {}".format(order_id, project.name,
                                                                              delivery_order_attribute_name,
                                                                              delivery_order_number))
            except RuntimeError as e:
                error_list.append(str(e))

    except MoySkladError as e:
        error_list.append("Ошибка МойСклад: {}".format(str(e)))
        return False, change_list, error_list

    return True, change_list, error_list
