import json

from MSApi import MSApi, MSApiException, Expand, CustomerOrder
from django.core.files.base import ContentFile
from yandex_geocoder import Client, NothingFound, YandexGeocoderException

from .settings import get_delivery_map_generator_settings
from ..AutocleanStorage import autoclean_default_storage
from moy_sklad_utils import filters, auth
from moy_sklad_utils.custom_entity_utils import find_custom_entity, get_entity_element_names


class FillingOutError(RuntimeError):
    pass


class AddressError(FillingOutError):
    pass


def create_point_feature(feature_id, lon, lat, point_name, desc, color):
    return {
        'type': "Feature",
        'id': feature_id,
        'geometry': {
            'type': "Point",
            'coordinates': [lon, lat]
        },
        'properties': {
            'description': desc,
            'iconCaption': point_name,
            'marker-color': color
        }
    }

def authorize_yandex_maps_client(key):
    try:
        return Client(key)
    except ValueError as e:
        raise RuntimeError(str(e))


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


def get_actual_address_coordinates(actual_address, client):
    try:
        coordinates = client.coordinates(actual_address)
        return float(coordinates[0]), float(coordinates[1])
    except NothingFound:
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


class FeatureCollection:
    def __init__(self, map_name):
        self.map_name = map_name
        self.iter = 0
        self.features = []

    def add_new_feature(self, lon: float, lat: float, point_name: str, desc: str, color: str):
        self.features.append(create_point_feature(self.iter, lon, lat, point_name, desc, color))
        self.iter = self.iter + 1

    def make_data(self):
        return {
            'type': "FeatureCollection",
            'metadata': {
                'name': self.map_name,
            },
            "features": self.features
        }


def run(date):
    try:
        MSApi.set_access_token(auth.get_moy_sklad_token())
        generator_settings = get_delivery_map_generator_settings()

        projects_blacklist = get_entity_element_names(find_custom_entity(generator_settings.projects_blacklist))
        client = authorize_yandex_maps_client(generator_settings.yandexmaps_key)

        default_color = generator_settings.default_color
        delivery_time_missed_color = generator_settings.delivery_time_missed_color

        error_list = []

        map_name = date.strftime('%d.%m.%Y')
        feature_collection = FeatureCollection(map_name)

        for customer_order in filter(
                lambda order: contains_project_in_blacklist(order.get_project(), projects_blacklist),
                gen_customers_orders_per_day(date)):
            customer_order: CustomerOrder
            try:
                try:
                    customer_order_point = make_customer_order_point(customer_order, client)
                except FillingOutError as e:
                    error_list.append(str(e))
                    continue

                color = default_color if (customer_order_point.delivery_time is None) else delivery_time_missed_color
                lon, lat = customer_order_point.lon_lat
                point_name = format_point_name(customer_order_point.customer_order_name,
                                               customer_order_point.delivery_time)
                feature_collection.add_new_feature(lon, lat, point_name, customer_order_point.actual_address, color)

            except YandexGeocoderException as e:
                error_list.append(f"Yandex Maps API error: {e}")
            except MSApiException as e:
                error_list.append(f"Moy Sklad error: {e}")

        data_json = json.dumps(feature_collection.make_data())
        true_filename = autoclean_default_storage.save("DeliveryMap_{}.geojson".format(map_name),
                                                       ContentFile(data_json))
        return error_list, true_filename

    except RuntimeError as e:
        return [f"Error: {e}"], ""
    except MSApiException as e:
        return [f"Moy Sklad error: {e}"], ""
