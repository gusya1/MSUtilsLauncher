import json
from datetime import date
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase

from moy_sklad.exceptions import MoySkladError
from moy_sklad.model import (
    MoySkladAttributeInfo,
    MoySkladCustomerOrder,
    MoySkladMeta,
    MoySkladMetaField,
    MoySkladProject,
)
from moy_sklad_settings.models import MoySkladSettings

from delivery_map_loader.models import DeliveryMapPaletteSettings, PaletteItem
from delivery_map_loader.run import delivery_map_loader


PROJECT_ID = UUID("11111111-2222-3333-4444-555555555555")
ORDER_ID = UUID("66666666-7777-8888-9999-000000000000")
ATTRIBUTE_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
AGENT_ID = UUID("12345678-1234-1234-1234-123456781234")
ORGANIZATION_ID = UUID("87654321-8765-8765-8765-876543218765")


def make_meta(entity_type, entity_id):
    return MoySkladMeta(
        href="https://api.moysklad.ru/api/remap/1.2/entity/{}/{}".format(entity_type, entity_id),
        type=entity_type,
        mediaType="application/json",
    )


def make_project(name="Проект А"):
    return MoySkladProject(id=PROJECT_ID, meta=make_meta("project", PROJECT_ID), name=name)


def make_order(project=None):
    return MoySkladCustomerOrder(
        id=ORDER_ID,
        meta=make_meta("customerorder", ORDER_ID),
        name="12345",
        agent=MoySkladMetaField(meta=make_meta("counterparty", AGENT_ID)),
        organization=MoySkladMetaField(meta=make_meta("organization", ORGANIZATION_ID)),
        project=project,
    )


def make_attribute_info(name="deliveryOrderNumber"):
    return MoySkladAttributeInfo(
        id=ATTRIBUTE_ID,
        meta=make_meta("attribute", ATTRIBUTE_ID),
        name=name,
        type="integer",
    )


def make_properties(marker_color="#82cdff", icon_caption="12345 Заказ клиента", icon_content="2"):
    return {
        "description": "Тестовый маркер",
        "iconCaption": icon_caption,
        "iconContent": icon_content,
        "marker-color": marker_color,
    }


def make_geojson(properties_list):
    features = [
        {
            "type": "Feature",
            "id": index + 1,
            "geometry": {"type": "Point", "coordinates": [30.5234, 59.9406]},
            "properties": properties,
        }
        for index, properties in enumerate(properties_list)
    ]
    return json.dumps({
        "type": "FeatureCollection",
        "metadata": {"name": "test"},
        "features": features,
    }).encode("utf-8")


class DeliveryMapLoaderRunTests(TestCase):

    def setUp(self):
        MoySkladSettings.objects.create(
            api_token="test-token",
            delivery_order_attribute_name="deliveryOrderNumber",
        )
        palette = DeliveryMapPaletteSettings.objects.create()
        PaletteItem.objects.create(config=palette, color="#82cdff", project="Проект А")

        self.date = date(2026, 11, 18)
        self.project = make_project("Проект А")
        self.order = make_order(project=None)
        self.orders = [self.order]
        self.attribute_info = make_attribute_info()
        self.requested_order_filters = []
        self.requested_project_filters = []

    def _mock_walk_for_all(self, client, entity_class, **kwargs):
        if entity_class is MoySkladProject:
            self.requested_project_filters.append(kwargs.get("filter"))
            return iter([self.project])
        if entity_class is MoySkladCustomerOrder:
            self.requested_order_filters.append(kwargs.get("filter"))
            return iter(self.orders)
        raise AssertionError("Неожиданный класс сущности: {}".format(entity_class))

    def _run(self, geojson_data=None):
        with patch.object(delivery_map_loader.getters, "walk_for_all", side_effect=self._mock_walk_for_all), \
                patch.object(
                    delivery_map_loader.getters, "get_attibutes_for_entity", return_value=[self.attribute_info]
                ), \
                patch.object(delivery_map_loader.updaters, "update_entity") as mock_update:
            if geojson_data is None:
                geojson_data = make_geojson([make_properties()])
            result = delivery_map_loader.run(geojson_data, self.date)
        return result, mock_update

    def test_happy_path_updates_order(self):
        (ok, change_list, error_list), mock_update = self._run()

        self.assertTrue(ok)
        self.assertEqual(change_list, ["Заказ 12345: проект - 'Проект А', deliveryOrderNumber - 2"])
        self.assertEqual(error_list, [])
        self.assertEqual(mock_update.call_count, 1)
        _, order_id, updated_data = mock_update.call_args.args
        self.assertEqual(order_id, ORDER_ID)
        self.assertEqual(updated_data.project.meta, self.project.meta)
        self.assertEqual(len(updated_data.attributes), 1)
        self.assertEqual(updated_data.attributes[0].meta, self.attribute_info.meta)
        self.assertEqual(updated_data.attributes[0].value, 2)
        payload = json.loads(updated_data.model_dump_json(exclude_none=True))
        self.assertEqual(payload, {
            "project": {"meta": self.project.meta.model_dump()},
            "attributes": [{"meta": self.attribute_info.meta.model_dump(), "value": 2}],
        })

    def test_unknown_marker_color(self):
        geojson_data = make_geojson([make_properties(marker_color="#ffffff"), make_properties()])
        (ok, change_list, error_list), mock_update = self._run(geojson_data)

        self.assertTrue(ok)
        self.assertEqual(error_list, ["Цвет #ffffff не определён"])
        self.assertEqual(len(change_list), 1)
        self.assertEqual(mock_update.call_count, 1)

    def test_order_not_found(self):
        self.orders = []
        (ok, change_list, error_list), mock_update = self._run()

        self.assertTrue(ok)
        self.assertEqual(error_list, ["Заказ '12345' не найден"])
        self.assertEqual(change_list, [])
        mock_update.assert_not_called()

    def test_ambiguous_order_number(self):
        self.orders = [make_order(), make_order()]
        (ok, change_list, error_list), mock_update = self._run()

        self.assertTrue(ok)
        self.assertEqual(error_list, ["Неоднозначный номер заказа: 12345"])
        self.assertEqual(change_list, [])
        mock_update.assert_not_called()

    def test_project_already_filled(self):
        self.order = make_order(project=MoySkladMetaField(meta=make_meta("project", PROJECT_ID)))
        self.orders = [self.order]
        (ok, change_list, error_list), mock_update = self._run()

        self.assertTrue(ok)
        self.assertEqual(error_list, ["Заказ 12345: Проект уже заполнен"])
        self.assertEqual(change_list, [])
        mock_update.assert_not_called()

    def test_put_error_is_per_feature(self):
        geojson_data = make_geojson([make_properties(), make_properties()])
        with patch.object(delivery_map_loader.getters, "walk_for_all", side_effect=self._mock_walk_for_all), \
                patch.object(
                    delivery_map_loader.getters, "get_attibutes_for_entity", return_value=[self.attribute_info]
                ), \
                patch.object(delivery_map_loader.updaters, "update_entity",
                             side_effect=MoySkladError("PUT failed")) as mock_update:
            ok, change_list, error_list = delivery_map_loader.run(geojson_data, self.date)

        self.assertTrue(ok)
        put_error = "Заказ 12345: Ошибка МойСклад: PUT failed"
        self.assertEqual(error_list, [put_error] * 2)
        self.assertEqual(change_list, [])
        self.assertEqual(mock_update.call_count, 2)

    def test_top_level_error_aborts(self):
        with patch.object(delivery_map_loader.getters, "walk_for_all", side_effect=self._mock_walk_for_all), \
                patch.object(delivery_map_loader.getters, "get_attibutes_for_entity",
                             side_effect=MoySkladError("API down")), \
                patch.object(delivery_map_loader.updaters, "update_entity") as mock_update:
            ok, change_list, error_list = delivery_map_loader.run(make_geojson([make_properties()]), self.date)

        self.assertFalse(ok)
        self.assertEqual(error_list, ["Ошибка МойСклад: API down"])
        self.assertEqual(change_list, [])
        mock_update.assert_not_called()

    def test_top_level_error_on_list_fetch_in_feature_loop(self):
        with patch.object(delivery_map_loader.getters, "walk_for_all", side_effect=MoySkladError("API down")), \
                patch.object(
                    delivery_map_loader.getters, "get_attibutes_for_entity", return_value=[self.attribute_info]
                ), \
                patch.object(delivery_map_loader.updaters, "update_entity") as mock_update:
            ok, change_list, error_list = delivery_map_loader.run(make_geojson([make_properties()]), self.date)

        self.assertFalse(ok)
        self.assertEqual(error_list, ["Ошибка МойСклад: API down"])
        self.assertEqual(change_list, [])
        mock_update.assert_not_called()

    def test_filter_strings(self):
        self._run()

        expected_order_filter = ("name=12345;deliveryPlannedMoment>=2026-11-18 00:00:00;"
                                 "deliveryPlannedMoment<2026-11-19 00:00:00")
        self.assertEqual(self.requested_order_filters, [expected_order_filter])
        self.assertEqual(self.requested_project_filters, ["name=Проект А"])
