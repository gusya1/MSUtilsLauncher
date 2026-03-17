import json
import logging

import ya_geocoder
from MSApi import MSApi, MSApiException, Expand, CustomerOrder
from django.core.files.base import ContentFile

from .settings import get_delivery_map_generator_settings
from ..AutocleanStorage import autoclean_default_storage
from moy_sklad_utils import filters, auth
from moy_sklad_utils.custom_entity_utils import find_custom_entity, get_entity_element_names
from ya_geocoder.client import Client
from ya_geocoder.exceptions import NothingFonudError


class FillingOutError(RuntimeError):
    pass


class AddressError(FillingOutError):
    pass


def authorize_yandex_maps_client(key):
    return Client(key)


def contains_project_in_blacklist(project, blacklist):
    return project is not None and project.get_name() in blacklist


def get_delivery_time_value(customer_order):
    delivery_time = customer_order.get_attribute_by_name('Время доставки')
    if delivery_time is None:
        return None
    else:
        return delivery_time.get_value()


def get_agent_actual_address(agent):
    actual_address = agent.get_actual_address()
    if actual_address is None:
        raise AddressError("Адрес не заполнен")
    return actual_address


def get_actual_address_coordinates(actual_address, client: Client):
    try:
        coordinates = client.get_coordinates(actual_address)
        return float(coordinates[0]), float(coordinates[1])
    except NothingFonudError:
        raise AddressError("Адрес не найден на карте")


class CustomerOrderPointOnMap:
    def __init__(self):
        self.customer_order_name = None
        self.delivery_time = None
        self.actual_address = None
        self.lon_lat = None


def make_customer_order_point(customer_order, client):
    result = CustomerOrderPointOnMap()
    result.customer_order_name = customer_order.get_name()
    result.delivery_time = get_delivery_time_value(customer_order)
    agent = customer_order.get_agent()
    try:
        result.actual_address = get_agent_actual_address(agent)
        result.lon_lat = get_actual_address_coordinates(result.actual_address, client)
    except AddressError as e:
        raise FillingOutError("Контрагент [{}]: {}".format(agent.get_name(), str(e)))
    return result


def gen_customers_orders_per_day(date):
    date_filter = filters.get_one_day_filter('deliveryPlannedMoment', date)
    return CustomerOrder.gen_list(filters=date_filter, expand=Expand('agent', 'project'))


def format_point_name(customer_order_name, delivery_time):
    return "{} ({})".format(customer_order_name, delivery_time)


class ColorManager:
    def __init__(self, default_color: str, delivery_time_missed_color: str):
        self.default_color = default_color
        self.delivery_time_missed_color = delivery_time_missed_color

    def get_color(self, delivery_time):
        if delivery_time is None:
            return self.delivery_time_missed_color
        return self.default_color


class Feature:
    def __init__(self):
        self.feature_id = None
        self.lon = None
        self.lat = None
        self.icon_caption = None
        self.icon_content = None
        self.desc = None
        self.color = None

    def make_data(self):
        return {
            'type': "Feature",
            'id': self.feature_id,
            'geometry': {
                'type': "Point",
                'coordinates': [self.lon, self.lat]
            },
            'properties': {
                'description': self.desc,
                'iconCaption': self.icon_caption,
                "iconContent": self.icon_content,
                'marker-color': self.color
            }
        }


class FeatureCollection:
    def __init__(self, map_name):
        self.map_name = map_name
        self.__iter = 0
        self.features = []

    def add_new_feature(self, feature: Feature):
        feature.feature_id = self.__iter
        self.features.append(feature)
        self.__iter += 1

    def make_data(self):
        return {
            'type': "FeatureCollection",
            'metadata': {
                'name': self.map_name,
            },
            "features": list(feature.make_data() for feature in self.features)
        }


def run(date):
    try:
        MSApi.set_access_token(auth.get_moy_sklad_token())
        generator_settings = get_delivery_map_generator_settings()

        projects_blacklist = get_entity_element_names(find_custom_entity(generator_settings.projects_blacklist))
        client = authorize_yandex_maps_client(generator_settings.yandexmaps_key)

        color_manager = ColorManager(generator_settings.default_color, generator_settings.delivery_time_missed_color)

        error_list = []

        map_name = date.strftime('%d.%m.%Y')
        feature_collection = FeatureCollection(map_name)

        for customer_order in filter(
                lambda order: not contains_project_in_blacklist(order.get_project(), projects_blacklist),
                gen_customers_orders_per_day(date)):
            customer_order: CustomerOrder
            logging.info("Processing customer order {}".format(customer_order.get_name()))

            feature = Feature()
            try:
                try:
                    customer_order_point = make_customer_order_point(customer_order, client)

                    feature.color = color_manager.get_color(customer_order_point.delivery_time)
                    feature.lon, feature.lat = customer_order_point.lon_lat
                    feature.icon_caption = format_point_name(customer_order_point.customer_order_name,
                                                             customer_order_point.delivery_time)
                    feature.icon_content = "0"
                    feature.desc = customer_order_point.actual_address

                    feature_collection.add_new_feature(feature)

                except FillingOutError as e:
                    error_list.append(str(e))
                    continue

            except ya_geocoder.exceptions.ResponseError as e:
                error_list.append(f"Ошибка запроса Геокодера: {e}")
            except MSApiException as e:
                error_list.append(f"Moy Sklad error: {e}")

        data_json = json.dumps(feature_collection.make_data())
        true_filename = autoclean_default_storage.save("DeliveryMap_{}.geojson".format(map_name),
                                                       ContentFile(data_json))
        return error_list, true_filename

    except ya_geocoder.exceptions.YandexGeocoderError as e:
        return [f"Ошибка Яндекс Геокодера: {e}"], ""
    except RuntimeError as e:
        return [f"Ошибка выполнения: {e}"], ""
    except MSApiException as e:
        return [f"Ошибка работы с МойСклад: {e}"], ""
