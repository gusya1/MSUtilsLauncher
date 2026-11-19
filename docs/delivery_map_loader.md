# Загрузка карты доставки в МойСклад

Приложение `delivery_map_loader` загружает карту доставки из Yandex Maps Constructor (GeoJSON-файл) в МойСклад: для каждого маркера на карте заказу покупателя присваиваются проект и номер очередности доставки.

## Точка входа

- `views.IndexView` (`site/delivery_map_loader/views.py`) — форма выбора даты доставки и GeoJSON-файла; после отправки вызывает `run(geojson_data, date)` и показывает список изменений/ошибок.
- Контракт: `run(geojson_data, date) -> (ok, change_list, error_list)` (`site/delivery_map_loader/run/delivery_map_loader.py::run`).

## Палитра цвет → проект

`DeliveryMapPaletteSettings` + `PaletteItem` (`site/delivery_map_loader/models.py`) — singleton-настройки с набором пар «цвет маркера (из палитры Yandex Maps Constructor) → имя проекта МойСклада». Цвет маркера берётся из свойства `marker-color` feature.

## Обработка

Для каждого feature GeoJSON:

1. Номер заказа — первая часть `iconCaption` (до пробела).
2. Проект — по цвету маркера через палитру, затем поиск проекта в МС по имени (`find_project_by_name`).
3. Номер очередности доставки — `iconContent` (целое число); записывается в дополнительное поле заказа с названием из `MoySkladSettings.delivery_order_attribute_name`.
4. Заказ ищется в МС по номеру + окно выбранной даты (с 00:00:00 до 00:00:00 следующего дня): фильтр `name={номер};deliveryPlannedMoment>=YYYY-MM-DD HH:MM:SS;deliveryPlannedMoment<YYYY-MM-DD+1 HH:MM:SS` (`find_customer_order_by_name`, общий хелпер `moy_sklad.utils.get_one_day_filter`).
5. Если у заказа уже заполнен проект — feature пропускается с ошибкой, обновление не выполняется.
6. Иначе заказ обновляется: `project` (meta проекта) + атрибут очередности доставки со значением из `iconContent` (`update_customer_order`, модель `MoySkladCustomerOrderUpdate`).

Запросы к МС идут через локальный клиент `moy_sklad` (`MoySkladClient` + `getters`/`updaters`), токен — из `MoySkladSettings`.

## Контракт ошибок

- Ошибки отдельных feature (цвет не определён в палитре, проект не найден / неоднозначно, заказ не найден / неоднозначно, проект уже заполнен, ошибка обновления) попадают в `error_list`, обработка остальных feature продолжается, результат — `True`.
- Сбой API МойСклада при получении списков проектов/заказов или атрибутов — `MoySkladError`, не перехватываемый обработчиком конкретного feature (включая сбои внутри цикла по feature), поднимается на топ-уровень: `ok = False`, сообщение «Ошибка МойСклад: ...» в `error_list`.
