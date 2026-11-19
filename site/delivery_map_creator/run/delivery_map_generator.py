import json
import logging

from requests.exceptions import HTTPError
from django.core.files.base import ContentFile

from ..AutocleanStorage import autoclean_default_storage
from yandex_geocoder.client import Client
from yandex_geocoder.exceptions import NothingFonudError, ResponseError, YandexGeocoderError
from moy_sklad.client import MoySkladClient, make_url
from moy_sklad import getters, model
from moy_sklad.exceptions import MoySkladError
from moy_sklad.utils import get_one_day_filter
from moy_sklad_settings.models import MoySkladSettings
from moy_sklad_settings.utils import get_moy_sklad_token

from delivery_map_creator.models import DeliveryMapGeneratorSettings

class FillingOutError(RuntimeError):
    pass


class AddressError(FillingOutError):
    pass


def authorize_yandex_maps_client(key):
    return Client(key)


def contains_project_in_blacklist(project, blacklist):
    return project is not None and project.name in blacklist


def get_delivery_time_value(customer_order, delivery_time_attribute_name):
    attr = customer_order.find_attribute_by_name(delivery_time_attribute_name)
    if attr is None:
        return None
    else:
        return attr.value


def get_agent_actual_address(agent):
    actual_address = agent.actualAddress
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


def make_customer_order_point(customer_order, client, delivery_time_attribute_name):
    result = CustomerOrderPointOnMap()
    result.customer_order_name = customer_order.name
    result.delivery_time = get_delivery_time_value(customer_order, delivery_time_attribute_name)
    agent = customer_order.agent
    try:
        result.actual_address = get_agent_actual_address(agent)
        result.lon_lat = get_actual_address_coordinates(result.actual_address, client)
    except AddressError as e:
        raise FillingOutError("Контрагент [{}]: {}".format(agent.name, str(e)))
    return result


def gen_customers_orders_per_day(client, date):
    date_filter = get_one_day_filter('deliveryPlannedMoment', date)
    return list(getters.walk_for_all(
        client, model.MoySkladCustomerOrderExpandedAgentProject,
        filter=date_filter, expand="agent,project", limit=100))


def get_project_blacklist_names(client, dict_name):
    for entity in getters.walk_for_href(
            client, model.MoySkladCustomEntity,
            make_url("context/companysettings/metadata"), list_field="customEntities"):
        if entity.name == dict_name:
            return [element.name for element in
                    getters.walk_for_href(client, model.MoySkladCustomEntityElement,
                                          entity.entityMeta.href)]
    raise RuntimeError("Справочник {} не найден!".format(dict_name))


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
        ms_client = MoySkladClient(get_moy_sklad_token())
        generator_settings = DeliveryMapGeneratorSettings.get_solo()
        delivery_time_attribute_name = MoySkladSettings.get_solo().delivery_time_attribute_name

        projects_blacklist = get_project_blacklist_names(ms_client, generator_settings.project_blacklist_dict)
        yandex_client = authorize_yandex_maps_client(generator_settings.yandexmaps_key)

        color_manager = ColorManager(generator_settings.default_color, generator_settings.delivery_time_missed_color)

        error_list = []

        map_name = date.strftime('%d.%m.%Y')
        feature_collection = FeatureCollection(map_name)

        for customer_order in filter(
                lambda order: not contains_project_in_blacklist(order.project, projects_blacklist),
                gen_customers_orders_per_day(ms_client, date)):
            logging.info("Processing customer order {}".format(customer_order.name))

            feature = Feature()
            try:
                try:
                    customer_order_point = make_customer_order_point(
                        customer_order, yandex_client, delivery_time_attribute_name)

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

            except ResponseError as e:
                error_list.append(f"Ошибка запроса Геокодера: {e}")

        data_json = json.dumps(feature_collection.make_data())
        true_filename = autoclean_default_storage.save("DeliveryMap_{}.geojson".format(map_name),
                                                       ContentFile(data_json))
        return error_list, true_filename

    except YandexGeocoderError as e:
        return [f"Ошибка Яндекс Геокодера: {e}"], ""
    except RuntimeError as e:
        return [f"Ошибка выполнения: {e}"], ""
    except (MoySkladError, HTTPError) as e:
        return [f"Ошибка работы с МойСклад: {e}"], ""
