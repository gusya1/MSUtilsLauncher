import json
from datetime import date
from unittest.mock import patch
from uuid import UUID

import requests
from django.test import TestCase

from moy_sklad.exceptions import MoySkladError
from moy_sklad.model import (
    MoscowDateTime,
    MoySkladAttribute,
    MoySkladCustomEntity,
    MoySkladCustomEntityElement,
    MoySkladCustomerOrderExpandedAgentProject,
    MoySkaldCounterparty,
    MoySkladMeta,
    MoySkladMetaField,
    MoySkladProject,
)
from moy_sklad_settings.models import MoySkladSettings
from yandex_geocoder.exceptions import NothingFonudError, ResponseError, UnexpectedResponseError

from delivery_map_creator.models import DeliveryMapGeneratorSettings
from delivery_map_creator.run import delivery_map_generator


ORDER_ID = UUID("66666666-7777-8888-9999-000000000000")
AGENT_ID = UUID("12345678-1234-1234-1234-123456781234")
ORGANIZATION_ID = UUID("87654321-8765-8765-8765-876543218765")
PROJECT_ID = UUID("11111111-2222-3333-4444-555555555555")
ATTRIBUTE_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
CUSTOM_ENTITY_ID = UUID("99999999-8888-7777-6666-555555555555")
ELEMENT_ID = UUID("44444444-3333-2222-1111-000000000000")

DICT_NAME = "Черный список проектов для генерации карты"
DELIVERY_TIME_ATTRIBUTE_NAME = "Время доставки"
ADDRESS = "ул. Тестовая, д. 1"
COORDINATES = (30.5234, 59.9406)


def make_meta(entity_type, entity_id):
    return MoySkladMeta(
        href="https://api.moysklad.ru/api/remap/1.2/entity/{}/{}".format(entity_type, entity_id),
        type=entity_type,
        mediaType="application/json",
    )


def make_counterparty(name="Иванов", actual_address=ADDRESS):
    return MoySkaldCounterparty(
        id=AGENT_ID,
        meta=make_meta("counterparty", AGENT_ID),
        name=name,
        updated=MoscowDateTime(2026, 11, 18, 10, 0, 0),
        archived=False,
        actualAddress=actual_address,
    )


def make_project(name="СВ-Т"):
    return MoySkladProject(id=PROJECT_ID, meta=make_meta("project", PROJECT_ID), name=name)


def make_order(name="12345", project=None, counterparty=None, delivery_time_value=None):
    attributes = []
    if delivery_time_value is not None:
        attributes.append(MoySkladAttribute(
            id=ATTRIBUTE_ID,
            meta=make_meta("attribute", ATTRIBUTE_ID),
            name=DELIVERY_TIME_ATTRIBUTE_NAME,
            type="string",
            value=delivery_time_value,
        ))
    return MoySkladCustomerOrderExpandedAgentProject(
        id=ORDER_ID,
        meta=make_meta("customerorder", ORDER_ID),
        name=name,
        agent=counterparty or make_counterparty(),
        organization=MoySkladMetaField(meta=make_meta("organization", ORGANIZATION_ID)),
        project=project,
        attributes=attributes,
    )


def make_custom_entity(name=DICT_NAME):
    return MoySkladCustomEntity(
        id=CUSTOM_ENTITY_ID,
        meta=make_meta("customentity", CUSTOM_ENTITY_ID),
        name=name,
        entityMeta=MoySkladMeta(
            href="https://api.moysklad.ru/api/remap/1.2/entity/customentity/{}".format(CUSTOM_ENTITY_ID),
            type="customentity",
            mediaType="application/json",
        ),
    )


def make_custom_entity_element(name):
    return MoySkladCustomEntityElement(
        id=ELEMENT_ID,
        meta=make_meta("customentityelement", ELEMENT_ID),
        name=name,
    )


class DeliveryMapGeneratorRunTests(TestCase):

    def setUp(self):
        MoySkladSettings.objects.create(
            api_token="test-token",
            delivery_time_attribute_name=DELIVERY_TIME_ATTRIBUTE_NAME,
        )
        DeliveryMapGeneratorSettings.objects.create(
            project_blacklist_dict=DICT_NAME,
            yandexmaps_key="yandex-key",
            default_color="#ff0000",
            delivery_time_missed_color="#00ff00",
        )

        self.date = date(2026, 11, 18)
        self.custom_entity = make_custom_entity()
        self.blacklist_elements = [make_custom_entity_element("СВ-Т")]
        self.orders = [make_order(delivery_time_value="10:00")]
        self.address_errors = {}
        self.requested_addresses = []
        self.requested_order_kwargs = []
        self.requested_metadata_kwargs = []
        self.requested_element_hrefs = []

    def _mock_walk_for_all(self, client, entity_class, **kwargs):
        if entity_class is MoySkladCustomerOrderExpandedAgentProject:
            self.requested_order_kwargs.append(kwargs)
            return iter(self.orders)
        raise AssertionError("Неожиданный класс сущности: {}".format(entity_class))

    def _mock_walk_for_href(self, client, entity_class, href, **kwargs):
        if entity_class is MoySkladCustomEntity:
            self.requested_metadata_kwargs.append(kwargs)
            return iter([self.custom_entity])
        if entity_class is MoySkladCustomEntityElement:
            self.requested_element_hrefs.append(href)
            return iter(self.blacklist_elements)
        raise AssertionError("Неожиданный класс сущности: {}".format(entity_class))

    def _mock_get_coordinates(self, address, **kwargs):
        self.requested_addresses.append(address)
        error = self.address_errors.get(address)
        if error is not None:
            raise error
        return COORDINATES

    def _run(self, walk_for_all_side_effect=None, walk_for_href_side_effect=None):
        with patch.object(delivery_map_generator.getters, "walk_for_all",
                          side_effect=walk_for_all_side_effect or self._mock_walk_for_all), \
                patch.object(delivery_map_generator.getters, "walk_for_href",
                             side_effect=walk_for_href_side_effect or self._mock_walk_for_href), \
                patch.object(delivery_map_generator.Client, "get_coordinates",
                             side_effect=self._mock_get_coordinates), \
                patch.object(delivery_map_generator.autoclean_default_storage, "save",
                             return_value="DeliveryMap_18.11.2026.geojson") as mock_save:
            result = delivery_map_generator.run(self.date)
        return result, mock_save

    def _saved_geojson(self, mock_save):
        filename, content = mock_save.call_args.args
        self.assertEqual(filename, "DeliveryMap_18.11.2026.geojson")
        raw = content.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    # --- happy path и содержимое GeoJSON ---

    def test_happy_path(self):
        (error_list, true_filename), mock_save = self._run()

        self.assertEqual(error_list, [])
        self.assertEqual(true_filename, "DeliveryMap_18.11.2026.geojson")
        data = self._saved_geojson(mock_save)
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(data["metadata"]["name"], "18.11.2026")
        features = data["features"]
        self.assertEqual(len(features), 1)
        feature = features[0]
        self.assertEqual(feature["geometry"]["coordinates"], list(COORDINATES))
        properties = feature["properties"]
        self.assertEqual(properties["iconCaption"], "12345 (10:00)")
        self.assertEqual(properties["description"], ADDRESS)
        self.assertEqual(properties["marker-color"], "#ff0000")
        self.assertEqual(self.requested_addresses, [ADDRESS])

    # --- blacklist проектов ---

    def test_blacklisted_project_is_skipped(self):
        self.orders = [make_order(project=make_project("СВ-Т"), delivery_time_value="10:00")]
        (error_list, true_filename), mock_save = self._run()

        self.assertEqual(error_list, [])
        data = self._saved_geojson(mock_save)
        self.assertEqual(data["features"], [])
        self.assertEqual(self.requested_addresses, [])

    def test_blacklist_requests_and_element_names(self):
        (error_list, true_filename), mock_save = self._run()

        self.assertEqual(error_list, [])
        metadata_kwargs = self.requested_metadata_kwargs[0]
        self.assertEqual(metadata_kwargs.get("list_field"), "customEntities")
        self.assertEqual(self.requested_element_hrefs, [self.custom_entity.entityMeta.href])
        # имена элементов справочника используются в проверке: заказ с проектом СВ-Т пропускается
        self.orders = [make_order(project=make_project("СВ-Т"))]
        (error_list, true_filename), mock_save = self._run()
        data = self._saved_geojson(mock_save)
        self.assertEqual(data["features"], [])

    # --- ошибки адреса контрагента ---

    def test_counterparty_without_actual_address(self):
        self.orders = [make_order(counterparty=make_counterparty(actual_address=None))]
        (error_list, true_filename), mock_save = self._run()

        self.assertEqual(error_list, ["Контрагент [Иванов]: Адрес не заполнен"])
        data = self._saved_geojson(mock_save)
        self.assertEqual(data["features"], [])
        self.assertEqual(self.requested_addresses, [])

    def test_yandex_nothing_found(self):
        self.address_errors[ADDRESS] = NothingFonudError('Nothing found for "{}" not found'.format(ADDRESS))
        (error_list, true_filename), mock_save = self._run()

        self.assertEqual(error_list, ["Контрагент [Иванов]: Адрес не найден на карте"])
        data = self._saved_geojson(mock_save)
        self.assertEqual(data["features"], [])

    # --- ошибки геокодера ---

    def test_yandex_response_error_is_per_order(self):
        second_address = "ул. Вторая, д. 2"
        self.orders = [
            make_order(delivery_time_value="10:00"),
            make_order(name="67890", counterparty=make_counterparty(name="Петров", actual_address=second_address),
                       delivery_time_value="11:00"),
        ]
        self.address_errors[ADDRESS] = ResponseError("Bad request")
        (error_list, true_filename), mock_save = self._run()

        self.assertEqual(error_list, ["Ошибка запроса Геокодера: Bad request"])
        data = self._saved_geojson(mock_save)
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(data["features"][0]["properties"]["iconCaption"], "67890 (11:00)")

    def test_yandex_unexpected_response_error_is_top_level(self):
        self.address_errors[ADDRESS] = UnexpectedResponseError("status_code=500")
        (error_list, true_filename), mock_save = self._run()

        self.assertEqual(error_list, ["Ошибка Яндекс Геокодера: status_code=500"])
        self.assertEqual(true_filename, "")
        mock_save.assert_not_called()

    # --- время доставки ---

    def test_missing_delivery_time_attribute(self):
        self.orders = [make_order()]
        (error_list, true_filename), mock_save = self._run()

        self.assertEqual(error_list, [])
        data = self._saved_geojson(mock_save)
        feature = data["features"][0]
        self.assertEqual(feature["properties"]["marker-color"], "#00ff00")
        self.assertEqual(feature["properties"]["iconCaption"], "12345 (None)")

    # --- сбои при получении справочника и заказов ---

    def test_blacklist_dict_not_found(self):
        def walk_for_href_side_effect(client, entity_class, href, **kwargs):
            if entity_class is MoySkladCustomEntity:
                return iter([])
            raise AssertionError("Неожиданный класс сущности: {}".format(entity_class))

        (error_list, true_filename), mock_save = self._run(walk_for_href_side_effect=walk_for_href_side_effect)

        self.assertEqual(error_list, ["Ошибка выполнения: Справочник {} не найден!".format(DICT_NAME)])
        self.assertEqual(true_filename, "")
        mock_save.assert_not_called()

    def test_moy_sklad_error_on_blacklist_fetch(self):
        (error_list, true_filename), mock_save = self._run(walk_for_href_side_effect=MoySkladError("API down"))

        self.assertEqual(error_list, ["Ошибка работы с МойСклад: API down"])
        self.assertEqual(true_filename, "")
        mock_save.assert_not_called()

    def test_moy_sklad_error_on_orders_fetch(self):
        (error_list, true_filename), mock_save = self._run(walk_for_all_side_effect=MoySkladError("API down"))

        self.assertEqual(error_list, ["Ошибка работы с МойСклад: API down"])
        self.assertEqual(true_filename, "")
        mock_save.assert_not_called()

    def test_http_error_on_orders_fetch(self):
        response = requests.Response()
        response.status_code = 500
        error = requests.exceptions.HTTPError("500 Server Error", response=response)
        (error_list, true_filename), mock_save = self._run(walk_for_all_side_effect=error)

        self.assertEqual(error_list, ["Ошибка работы с МойСклад: 500 Server Error"])
        self.assertEqual(true_filename, "")
        mock_save.assert_not_called()

    # --- параметры запроса к заказам ---

    def test_orders_request_parameters(self):
        self._run()

        kwargs = self.requested_order_kwargs[0]
        self.assertEqual(kwargs["filter"],
                         "deliveryPlannedMoment>=2026-11-18 00:00:00;deliveryPlannedMoment<2026-11-19 00:00:00")
        self.assertEqual(kwargs["expand"], "agent,project")
        self.assertEqual(kwargs["limit"], 100)
