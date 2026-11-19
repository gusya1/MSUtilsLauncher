# План: перевод delivery_map_creator с легаси MSApi на локальный moy_sklad

Дата: 2026-11-19
Статус: согласован, ожидает реализации

## Контекст

`site/delivery_map_creator/run/delivery_map_generator.py` работает через легаси библиотеку MSApi (глобальный токен `MSApi.set_access_token`, `CustomerOrder.gen_list(filters=..., expand=Expand('agent', 'project'))`, `MSApiException`) и legacy-хелперы `moy_sklad_utils.filters.get_one_day_filter` / `moy_sklad_utils.custom_entity_utils.find_custom_entity/get_entity_element_names` (оба на MSApi). Проект переходит на локальный клиент `site/moy_sklad/`; эталоны перевода — уже переведённые `delivery_map_loader` (полностью без MSApi, есть тесты) и `delivery_distributor` (expand-запросы, имена атрибутов из `MoySkladSettings`).

Ключевые факты:

- Токена глобально нет: `client = MoySkladClient(get_moy_sklad_token())`, клиент передаётся в хелперы.
- Фильтры — обычные строки (urlencode'ятся при запросе), а не объекты `Filter`.
- `expand=agent,project` для коллекции customerorder возвращает полные inline-объекты контрагента и проекта: подтверждено официальным OpenAPI-спеком МойСклада (референсные поля agent/project, общий механизм expand) и работающим legacy-кодом MSApi 0.2.11 (`Expand('agent','project')` → query-param `expand=agent,project`).
- Контрагент: поле `actualAddress` — String(255), может отсутствовать (legacy `Counterparty.get_actual_address()` читает именно его). В доках МС agent заказа — ссылка на контрагента; модель контрагента defensively валидирует и форму юрлица (`id/meta/name/updated/archived` присутствуют у любой сущности МС, `email/phone/tags` имеют дефолты), отсутствие `actualAddress` даёт тот же исход, что и в legacy («Адрес не заполнен»).
- Пользовательские справочники: GET `context/companysettings/metadata` → массив `customEntities[]`, у элемента поля `id`, `meta`, `name`, `entityMeta` (href на коллекцию элементов); элементы — по `entityMeta.href`, строки с полем `name`. Подтверждено OpenAPI-спеком и legacy-кодом (`CompanySettings.gen_custom_entities()`, `CustomEntity.gen_elements()`).
- Legacy-семантика, которую сохраняем:
  - окно дня: `deliveryPlannedMoment>=YYYY-MM-DD HH:MM:SS;deliveryPlannedMoment<YYYY-MM-DD+1 HH:MM:SS` (legacy `DateTimeFilter.gte/lt`, формат `%Y-%m-%d %H:%M:%S`);
  - при expand лимит страницы — 100 (`MSLowApi.gen_objects` снижает limit до 100 при наличии expand);
  - blacklist-проекты: имена элементов справочника из `DeliveryMapGeneratorSettings.project_blacklist_dict`, заказ пропускается, если имя его проекта в списке;
  - тексты ошибок и контрольный поток (см. ниже).

## Согласованные решения

1. Перевести `delivery_map_generator.py` на moy_sklad по паттерну переведённых приложений; сохранить контрольный поток, тексты ошибок и GeoJSON-формат (`Feature`/`FeatureCollection`).
2. Имя атрибута времени доставки — из `MoySkladSettings.delivery_time_attribute_name` (конвенция delivery_distributor; у delivery_map_loader аналогичный механизм для другого поля — `delivery_order_attribute_name`), а не хардкод «Время доставки».
3. Яндекс-геокодер без изменений: прямой `Client(key)` с ключом из `DeliveryMapGeneratorSettings.yandexmaps_key` — это не MSApi, вне скоупа перевода.
4. В `moy_sklad/getters.py` новых функций не добавлять (только абстрактные геттеры для любых сущностей): blacklist-справочник читается через существующие `walk_for_href`/`get_entities_by_href` (параметр `list_field`) в приватном хелпере приложения.
5. Хелпер окна дня вынести в общий код: `moy_sklad/utils.py::get_one_day_filter` (использует `format_moy_sklad_datetime`); приватная копия `_get_one_day_filter` из delivery_map_loader удаляется, приложение переключается на общий хелпер.
6. Добавить тесты `site/delivery_map_creator/tests.py` (Django TestCase + mock'нутые getters и Yandex-клиент, без сети).
7. Написать документацию `docs/delivery_map_creator.md` по факту.

## Реализация

### 1. `site/moy_sklad/model.py` (добавления)

- `MoySkaldCounterpartyBase`: добавить поле `actualAddress: str | None = None`.
- Новый класс расширенного заказа (паттерн `MoySkladCustomerOrderExpandedPositionsAssortment`, override полей в подклассе):
  ```python
  class MoySkladCustomerOrderExpandedAgentProject(MoySkladCustomerOrder):
      agent: MoySkaldCounterparty
      project: MoySkladProject | None = None
  ```
- Новые модели пользовательских справочников:
  ```python
  class MoySkladCustomEntity(BaseModel):
      id: UUID
      meta: MoySkladMeta
      name: str
      entityMeta: MoySkladMeta

  class MoySkladCustomEntityElement(BaseModel):
      id: UUID
      meta: MoySkladMeta
      name: str
  ```
- `types.py` не меняется: расширенный класс — подкласс `MoySkladCustomerOrder`, маппинг на `entity/customerorder` работает через issubclass.

### 2. `site/moy_sklad/utils.py` (общий хелпер окна дня)

```python
def get_one_day_filter(parameter, date):
    next_date = date + timedelta(days=1)
    return "{}>={};{}<{}".format(parameter, format_moy_sklad_datetime(date), parameter,
                                 format_moy_sklad_datetime(next_date))
```
(добавить импорт `timedelta`).

### 3. `site/delivery_map_loader/run/delivery_map_loader.py` (убрать дубль хелпера)

- Удалить приватный `_get_one_day_filter`;
- импорт: `from moy_sklad.utils import make_entity_meta_filed, get_one_day_filter` (`format_moy_sklad_datetime` из импорта убрать — после удаления хелпера не используется, ruff F401);
- удалить `from datetime import timedelta` (единственное использование — в удалённом хелпере, ruff F401);
- вызов: `date_filter = get_one_day_filter('deliveryPlannedMoment', date)` (строка фильтра не меняется).
- Тесты delivery_map_loader не трогаются (проверяют строку фильтра, а не функцию).

### 4. `site/delivery_map_creator/run/delivery_map_generator.py` (переписать)

Импорт:

- Убрать: MSApi (`MSApi`, `MSApiException`, `Expand`, `CustomerOrder`), `moy_sklad_utils.filters` и `moy_sklad_utils.custom_entity_utils` (`find_custom_entity`, `get_entity_element_names`).
- Добавить: `MoySkladClient`, `make_url` (`moy_sklad.client`), `getters`, `model` (`moy_sklad`), `MoySkladError` (`moy_sklad.exceptions`), `HTTPStatusError` (`requests.exceptions`), `get_one_day_filter` (`moy_sklad.utils`), `MoySkladSettings` (`moy_sklad_settings.models`).
- Сохранить: `autoclean_default_storage`, обёртку `authorize_yandex_maps_client(key)` (возвращает `Client(key)`) и Yandex-исключения, `get_moy_sklad_token`, `DeliveryMapGeneratorSettings`.

Функции (клиент — первый аргумент):

| Legacy | Новый moy_sklad |
|---|---|
| `MSApi.set_access_token(...)` | `client = MoySkladClient(get_moy_sklad_token())` в `run()` |
| `filters.get_one_day_filter('deliveryPlannedMoment', date)` (объект MSApi) | общий `get_one_day_filter('deliveryPlannedMoment', date)` — строка, та же семантика |
| `CustomerOrder.gen_list(filters=..., expand=Expand('agent','project'))` | `list(getters.walk_for_all(client, model.MoySkladCustomerOrderExpandedAgentProject, filter=date_filter, expand="agent,project", limit=100))` — материализуется до цикла (конвенция delivery_map_loader) |
| `get_entity_element_names(find_custom_entity(dict_name))` | приватный `get_project_blacklist_names(client, dict_name)` через `walk_for_href` (см. ниже); «Справочник {} не найден!» → `RuntimeError` (как legacy) |
| `order.get_attribute_by_name('Время доставки').get_value()` (None → None) | null-safe: `attr = order.find_attribute_by_name(name); attr.value if attr else None` (паттерн delivery_distributor), имя атрибута из `MoySkladSettings`; отсутствие атрибута → None → цвет missed, как в legacy |
| `agent = order.get_agent(); agent.get_actual_address()/get_name()` | `agent = order.agent`; `agent.actualAddress` / `agent.name` (полный inline-объект через expand) |
| `order.get_project().get_name()` в blacklist-проверке | `order.project.name`, сообщение/логика без изменений |

Приватный хелпер blacklist-справочника:

```python
def get_project_blacklist_names(client, dict_name):
    for entity in getters.walk_for_href(
            client, model.MoySkladCustomEntity,
            make_url("context/companysettings/metadata"), list_field="customEntities"):
        if entity.name == dict_name:
            return [element.name for element in
                    getters.walk_for_href(client, model.MoySkladCustomEntityElement,
                                          entity.entityMeta.href)]
    raise RuntimeError("Справочник {} не найден!".format(dict_name))
```

`run(date)`:

- Порядок операций как в legacy: клиент → `DeliveryMapGeneratorSettings.get_solo()` → blacklist (MS-запросы) → Yandex-клиент → ColorManager → список заказов → цикл.
- Имя атрибута времени доставки — из `MoySkladSettings.get_solo().delivery_time_attribute_name`, передаётся в `make_customer_order_point`.
- Per-order цикл без изменений по логике: blacklist-проверка → точка (имя, время доставки, адрес контрагента, координаты) → feature; тексты ошибок сохраняются дословно.
- Исключения:
  - per-order: `FillingOutError` («Контрагент [{}]: Адрес не заполнен / Адрес не найден на карте») → в `error_list`, цикл продолжается; `ResponseError` → «Ошибка запроса Геокодера: {e}», цикл продолжается.
  - per-order except MSApi-ошибки убирается как недостижимый: legacy-генератор `gen_list` ленивый, сбой страницы возникал в операторе `for`, вне per-order try (MS-вызовов внутри тела цикла при expand нет) — топ-level аборт при fetch-сбое это точный parity с legacy.
  - топ-level: `YandexGeocoderError` → `[f"Ошибка Яндекс Геокодера: {e}"], ""`; `RuntimeError` (включая «Справочник не найден») → `[f"Ошибка выполнения: {e}"], ""`; `MoySkladError` и `requests.HTTPStatusError` (сбои при получении справочника/элементов/заказов; HTTPStatusError — статусы вне 401/400/412, которые `getters.raise_for_status` не оборачивает в MoySkladError) → `[f"Ошибка работы с МойСклад: {e}"], ""`.
- Контракт возврата `(error_list, true_filename)` и сохранение GeoJSON в `autoclean_default_storage` без изменений.

### 5. `site/delivery_map_creator/tests.py` (новый файл)

Django TestCase по паттерну `delivery_map_loader/tests.py`: в setUp создаются `MoySkladSettings` (`api_token`, `delivery_time_attribute_name="Время доставки"`) и `DeliveryMapGeneratorSettings` (`project_blacklist_dict`, `yandexmaps_key`, цвета); mock'уются `getters.walk_for_all`, `getters.walk_for_href`, Yandex-клиент (`Client.get_coordinates`) и `autoclean_default_storage.save`. Фикстуры заказов — `MoySkladCustomerOrderExpandedAgentProject` с inline-контрагентом (с/без `actualAddress`) и проектом.

Тесты:

1. Happy path → feature с правильным цветом, координатами, iconCaption «имя (время)», desc = адрес; файл сохранён, GeoJSON корректен; error_list пуст.
2. Заказ с blacklist-проектом → пропускается, feature не добавляется.
3. Контрагент без `actualAddress` → «Контрагент [{}]: Адрес не заполнен».
4. Yandex `NothingFonudError` → «Контрагент [{}]: Адрес не найден на карте».
5. Yandex `ResponseError` per-order → «Ошибка запроса Геокодера: ...», остальные заказы обработаны.
6. Атрибут времени доставки отсутствует → цвет `delivery_time_missed_color`, iconCaption «имя (None)» (поведение legacy).
7. Справочник blacklist не найден → RuntimeError → `[f"Ошибка выполнения: Справочник {} не найден!"], ""`.
8. `MoySkladError` и `requests.HTTPStatusError` при получении списка заказов → `[f"Ошибка работы с МойСклад: ..."], ""`, файл не сохраняется.
9. Проверка запроса к заказам: filter-строка окна дня, `expand="agent,project"`, limit=100.
10. Blacklist: `walk_for_href` по metadata (`list_field="customEntities"`) + элементы по `entityMeta.href`; имена элементов используются в проверке.
11. Yandex `UnexpectedResponseError` (статус вне 200/403/429/400) → топ-level ветка `YandexGeocoderError`: `[f"Ошибка Яндекс Геокодера: ..."], ""`, файл не сохраняется.
12. `MoySkladError` при получении blacklist-справочника/элементов (`walk_for_href`) → `[f"Ошибка работы с МойСклад: ..."], ""`, файл не сохраняется.

## Актуализация документации

- Написать `docs/delivery_map_creator.md`: только бизнес-логика — назначение приложения (создание карты доставки на выбранный день: GeoJSON с точками заказов для Yandex Maps), точка входа (`views.IndexView` → `run(date)`), blacklist проектов через пользовательский справочник МС, адрес точки — фактический адрес контрагента заказа, время доставки из дополнительного поля (имя из `MoySkladSettings`), цвета маркеров; контракт ошибок; ключевые файлы/классы: `run/delivery_map_generator.py::run`, `views.IndexView`. Механика реализации в доки не выносится.
- Обновить `docs/delivery_map_loader.md`: ссылка на `_get_one_day_filter` (пункт про фильтр окна дня) заменить на общий хелпер `moy_sklad.utils.get_one_day_filter` — после удаления приватной копии документ должен описывать фактическое состояние.
- Документация описывает только фактическое состояние репозитория; история изменений — в этом файле плана.

## Проверка (по §8 AGENTS.md)

Миграции не требуются (модели Django не меняются):

```
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web pytest moy_sklad -v --reuse-db --nomigrations
docker compose exec web pytest delivery_map_loader -v --reuse-db --nomigrations
docker compose exec web pytest delivery_map_creator -v --reuse-db --nomigrations
docker compose exec web ruff check delivery_map_loader
docker compose exec web ruff check delivery_map_creator
docker compose exec web ruff check moy_sklad
```

## Риски и что не делаем

- `moy_sklad_utils/filters.py` и `custom_entity_utils.py` остаются legacy (на MSApi) — ими пользуются ещё 3 непереведённых приложения (demand_creator, processing_creator, accounts_synchronize); общий хелпер окна дня вынесен в `moy_sklad/utils.py`, при переводе остальных приложений legacy-модуль удаляется.
- Per-order except MSApi-ошибки в legacy был недостижим для fetch-сбоев (ленивый генератор: сбой страницы возникал вне per-order try) — новый топ-level аборт «Ошибка работы с МойСклад» при получении списка заказов это точный parity, а не изменение поведения.
- `requests.HTTPStatusError` (статусы вне 401/400/412) перехватывается на топ-level только в этом приложении; другие переведённые приложения (delivery_map_loader и др.) имеют тот же пробел — выравнивание конвенции выносится за скоуп.
- `pydantic.ValidationError` при неожиданной форме JSON МС не перехватывается (тот же пробел у delivery_map_loader) — конвенционно согласовано.
- `walk_for_href` шлёт параметры limit/offset, которых legacy не отправлял ни на эндпоинте metadata (в доках МС для него query-параметры не описаны), ни на коллекции элементов справочника; прецедент в кодовой базе — `get_states_for_entity` (production). Перед реализацией проверить живым запросом оба эндпоинта.
- Крайние случаи без дружелюбного сообщения, но с parity к legacy: отсутствие/null обязательных полей заказа (`agent`, `organization`, `name`) — legacy падает AttributeError при обращении, новый код — pydantic.ValidationError при материализации; `ReadTimeout` (не подкласс ConnectionError, не оборачивается клиентом) → необработанный сбой в обоих вариантах.
- `limit=100` при expand — parity с legacy (delivery_distributor использует 99 для более тяжёлого расширения positions).
- Agent заказа в доках МС — ссылка на контрагента; если встретится форма юрлица, модель контрагента её валидирует (общие поля `id/meta/name/updated/archived`), у юрлица `actualAddress` отсутствует → «Адрес не заполнен», как в legacy.
- Поле `DeliveryMapGeneratorSettings.yandexmaps_key` остаётся и используется (Yandex-клиент без изменений).
- Повторные запросы blacklist-справочника не кэшируем — один вызов на `run()`, поведение идентично legacy.
