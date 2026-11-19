# План: перевод delivery_map_loader с легаси MSApi на локальный moy_sklad

Дата: 2026-11-18
Статус: согласован, ожидает реализации

## Контекст

`site/delivery_map_loader/run/delivery_map_loader.py` работает через легаси библиотеку MSApi (глобальный токен `MSApi.set_access_token`, объекты `Filter`, `auch_put`). Проект переходит на локальный клиент `site/moy_sklad/` (`MoySkladClient` + `getters`/`updaters`/`model`); эталон перевода — уже переведённое `site/courier_data_loader/core/loader.py` с тем же набором функций (поиск проекта/заказа по имени, обновление заказа project + attributes).

Ключевые факты нового клиента:

- Токена глобально нет: `client = MoySkladClient(get_moy_sklad_token())`, клиент передаётся в хелперы.
- Фильтры — обычные строки: `getters.walk_for_all(client, cls, filter="name=X;...")` (urlencode'ятся при запросе), а не объекты `Filter`.
- Обновление сущности: `updaters.update_entity(client, id, pydantic_model)` — PUT JSON с `exclude_none`; для заказа маппится на `entity/customerorder/{id}` (`site/moy_sklad/types.py`).
- Исключения клиента — все наследники `MoySkadError` (connection / rate limit / 401 / 400/412).
- Семантика legacy-фильтра дня: `Filter.eq("name", X)` + `get_one_day_filter('deliveryPlannedMoment', date)` → `name=X;deliveryPlannedMoment>=YYYY-MM-DD;deliveryPlannedMoment<YYYY-MM-DD+1` (для объекта `date` `str()` даёт ISO-дату).
- Контракт view не меняется: `run(geojson_data, date) -> (ok, change_list, error_list)` (`site/delivery_map_loader/views.py`).

## Согласованные решения

1. Перевести `delivery_map_loader.py` на moy_sklad по паттерну `courier_data_loader/core/loader.py`; сохранить контрольный поток, тексты ошибок и JSON-форму PUT.
2. Вместе перевести `run/projects.py::get_project_names` (тоже legacy MSApi; в views.py импортируется, но не используется) — после этого приложение полностью без MSApi.
3. Добавить тесты `site/delivery_map_loader/tests.py` (Django TestCase + mock'нутые `getters`/`updaters`, без сети).
4. Написать документацию `docs/delivery_map_loader.md` по факту (документации по приложению нет).

## Реализация

### 1. `site/delivery_map_loader/run/delivery_map_loader.py` (переписать)

Импорт:

- Убрать: MSApi (`Project`, `CustomerOrder`, `MSApi`, `error_handler`, `MSApiException`, `MSApiHttpException`, `Filter`) и `moy_sklad_utils.filters`.
- Добавить: `MoySkladClient`, `getters`, `model`, `updaters` (из `moy_sklad`), `MoySkladError` (`moy_sklad.exceptions`), `make_entity_meta_filed` (`moy_sklad.utils`).
- Сохранить: `MoySkladSettings`, `get_moy_sklad_token`, `DeliveryMapPaletteSettings`, классы `map_constructor_model`.

Функции (клиент — первый аргумент):

| Legacy | Новый moy_skad |
|---|---|
| `MSApi.set_access_token(...)` | `client = MoySkladClient(get_moy_sklad_token())` в `run()` |
| `_get_one_day_filter(parameter, date)` (новый приватный хелпер) | строка `{parameter}>=YYYY-MM-DD;{parameter}<YYYY-MM-DD+1` — та же семантика legacy-фильтра дня |
| `find_project_by_name(name)` через `Project.gen_list(Filter.eq("name", ...))` | `getters.walk_for_all(client, model.MoySkladProject, filter="name={}")` |
| `find_customer_order_by_name(order_id, date_filter)` | `getters.walk_for_all(client, model.MoySkladCustomerOrder, filter="name={};{date_filter}")` |
| `find_customer_order_attribute_by_name(name)` через `CustomerOrder.gen_attributes_list()` | `getters.get_attibutes_for_entity(client, model.MoySkladCustomerOrder)` (опечатка в имени — существующая в кодовой базе) |
| `check_customer_order_project(order)`: `order.get_project() is not None` | `order.project is not None`, сообщение «Заказ {}: Проект уже заполнен» сохраняется |
| `update_customer_order(id, dict)` через `MSApi.auch_put` | `model.MoySkladCustomerOrderUpdate(project=make_entity_meta_filed(project), attributes=[MoySkladAttributeCreate(meta=attr.meta, value=n)])` + `updaters.update_entity(client, order.id, updated_data)`; `MoySkladError` → `RuntimeError("Заказ {}: Ошибка МойСклад: {}")` |

`run(geojson_data, date)`:

- Per-feature цикл без изменений по логике: properties → order_id из iconCaption → проект по цвету палитры → номер очередности из iconContent → поиск заказа (name + окно дня) → проверка «проект уже заполнен» → PUT.
- Топ-уровень: вместо трёх legacy-except (`MSApiHttpException`, `MSApiException`, `FileNotFoundError`) — один `except MoySkladError` → `error_list.append("Ошибка МойСклад: {}")`, return False.
- Контракт возврата `(ok, change_list, error_list)` и все тексты ошибок сохраняются.

Сохраняется контрольный поток legacy: per-feature `RuntimeError` (не найден / неоднозначно / проект уже заполнен / ошибка PUT) → в `error_list`, цикл продолжается; сбой API при получении списков/атрибутов (вне per-feature catch) → аборт с False.

JSON-форма PUT идентична legacy: `{"project": {"meta": ...}, "attributes": [{"meta": ..., "value": n}]}` — в `MoySkladCustomerOrderUpdate` поля `agent`/`organization` = None и исключаются при сериализации (`exclude_none`).

### 2. `site/delivery_map_loader/run/projects.py` (удалить)

Удалить вместе с использованиями

### 3. `site/delivery_map_loader/tests.py` (новый файл)

Django TestCase: в setUp создаются `MoySkladSettings` (api_token + delivery_order_attribute_name), `DeliveryMapPaletteSettings` + `PaletteItem` (цвет → имя проекта); mock'уются `getters.walk_for_all`, `getters.get_attibutes_for_entity`, `updaters.update_entity`. GeoJSON-фикстура: FeatureCollection с 1–2 feature, properties — `iconCaption "12345 ..."`, `iconContent "2"`, `marker-color` из палитры.

Тесты:

1. Happy path → True, change_list заполнен, PUT вызван с правильным id и моделью (meta проекта + значение атрибута).
2. Неизвестный цвет маркера → «Цвет {} не определён» в error_list, остальные feature обработаны, результат True.
3. Заказ не найден → «Заказ '{}' не найден».
4. Неоднозначный номер заказа (2 строки) → «Неоднозначный номер заказа: {}».
5. Проект уже заполнен у заказа → «Проект уже заполнен», PUT не вызывается.
6. `MoySkladError` при PUT → per-feature ошибка, цикл продолжается.
7. `MoySkladError` при получении списков/атрибутов (топ-уровень) → False + «Ошибка МойСклад: ...».
8. Проверка строки фильтра запроса к заказам: `name={};deliveryPlannedMoment>=YYYY-MM-DD;deliveryPlannedMoment<YYYY-MM-DD+1`.

## Актуализация документации

- Написать `docs/delivery_map_loader.md`: только бизнес-логика — назначение приложения (загрузка карты доставки из Yandex Maps Constructor в МойСклад), палитра цвет→проект (`DeliveryMapPaletteSettings`/`PaletteItem`), идентификация заказа по номеру из iconCaption, заполнение проекта и атрибута очередности доставки у заказов на выбранную дату, контракт ошибок; ключевые файлы/классы: `run/delivery_map_loader.py::run`, `views.IndexView`. Механика реализации (MRO, kwargs, устройство виджетов) в доки не выносится.
- Документация описывает только фактическое состояние репозитория; история изменений — в этом файле плана.

## Проверка (по §8 AGENTS.md)

Миграции не требуются (модели не меняются):

```
docker compose exec web python manage.py check
docker compose exec web pytest delivery_map_loader -v --reuse-db --nomigrations
docker compose exec web ruff check delivery_map_loader
```

## Риски и что не делаем

- `moy_sklad_utils/filters.py` остаётся legacy (на MSApi) — им пользуются ещё 4 непереведённых приложения (demand_creator, processing_creator, accounts_synchronize, delivery_map_creator); хелпер окна дня дублируется приватной функцией в модуле приложения. При переводе остальных приложений вынести общий хелпер.
- Повторные одинаковые запросы «проект по имени» на каждый feature не кэшируем — поведение идентично legacy (N feature → N GET проекта); при необходимости оптимизировать позже.
- `FileNotFoundError` в топ-уровне legacy не воспроизводим: новый клиент файлы не читает, все ошибки клиента — наследники `MoySkladError`.
