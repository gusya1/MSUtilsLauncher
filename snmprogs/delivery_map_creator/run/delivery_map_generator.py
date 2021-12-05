import datetime
import json

import googlemaps
from MSApi import MSApi, MSApiException, DateTimeFilter, Expand, CustomerOrder
from MSApi import CompanySettings
from django.core.files.base import ContentFile
from googlemaps.exceptions import ApiError, HTTPError, Timeout, TransportError

from .settings import MOY_SKLAD, DELIVERY_MAP_GENERATOR
from ..AutocleanStorage import autoclean_default_storage


def create_point_feature(feature_id, lat, lon, point_name, desc, color):
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


def run(date):
    try:

        MSApi.set_access_token(MOY_SKLAD.TOKEN)

        for entity in CompanySettings.gen_custom_entities():
            if entity.get_name() != DELIVERY_MAP_GENERATOR.PROJECTS_BLACKLIST_ENTITY:
                continue
            projects_blacklist = list(entity_elem.get_name() for entity_elem in entity.gen_elements())
            break
        else:
            raise RuntimeError("Справочник {} не найден!".format(DELIVERY_MAP_GENERATOR.PROJECTS_BLACKLIST_ENTITY))

        error_list = []

        try:
            gmaps = googlemaps.Client(key=DELIVERY_MAP_GENERATOR.GOOGLEMAPS_KEY)
        except ValueError as e:
            raise RuntimeError(str(e))

        # date = datetime.datetime.combine(date, datetime.time())
        map_name = date.strftime('%d.%m.%Y')

        # создаём фильтр по дате
        date_filter = DateTimeFilter.gte('deliveryPlannedMoment', date)
        date_filter += DateTimeFilter.lt('deliveryPlannedMoment', date + datetime.timedelta(days=1))

        features_list = []
        features_iter = 0

        offset = 0
        for customer_order in CustomerOrder.gen_list(filters=date_filter, expand=Expand('agent', 'project')):
            customer_order: CustomerOrder
            try:
                project = customer_order.get_project()
                if project is not None:
                    if project.get_name() in projects_blacklist:
                        continue

                color = DELIVERY_MAP_GENERATOR.DEFAULT_COLOR

                delivery_time = customer_order.get_attribute_by_name('deliveryPlannedMoment')
                if delivery_time is None:
                    delivery_time = ""
                    color = DELIVERY_MAP_GENERATOR.DELIVERY_TIME_MISSED_COLOR

                agent = customer_order.get_agent()
                actual_address = agent.get_actual_address()
                if actual_address is None:
                    error_list.append(f"Контрагент [{agent.get_name()}]: Адрес не заполнен")
                    continue

                geocode_result = gmaps.geocode(actual_address)
                if len(geocode_result) == 0:
                    error_list.append(f"Контрагент [{agent.get_name()}]: Адрес не найден на карте")
                    continue
                if len(geocode_result) != 1:
                    error_list.append(f"Контрагент [{agent.get_name()}]: Неоднозначный адрес")
                    continue

                location = geocode_result[0].get('geometry').get('location')
                features_list.append(create_point_feature(
                    features_iter,
                    location.get('lat'),
                    location.get('lng'),
                    f"{customer_order.get_name()} ({delivery_time})",
                    actual_address,
                    color
                ))
                features_iter += 1

            except ApiError as e:
                error_list.append(f"Google Maps API error: {e}")
            except HTTPError as e:
                error_list.append(f"HTTP error: {e}")
            except Timeout as e:
                error_list.append(f"Timeout error: {e}")
            except TransportError as e:
                error_list.append(f"Transport error: {e}")
            except MSApiException as e:
                error_list.append(f"Moy Sklad error: {e}")


        geojson_point_collection = {
            'type': "FeatureCollection",
            'metadata': {
                'name': map_name,
            },
            "features": features_list
        }

        data_json = json.dumps(geojson_point_collection)
        true_filename = autoclean_default_storage.save("DeliveryMap_{}.geojson".format(map_name),
                                                       ContentFile(data_json))
        return error_list, true_filename

    except RuntimeError as e:
        return f"Error: {e}", ""
    except MSApiException as e:
        return f"Moy Sklad error: {e}", ""
