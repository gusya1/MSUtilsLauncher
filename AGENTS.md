# AGENTS.md - Project Notes for AI Agents

## 1. Обзор проекта

MSUtilsLauncher (snmprogs) - логистические утилиты интернет-магазина "Собака на мясе": интеграция с МойСкладом, маршрутизация доставки, планирование маршрутов курьеров.

### Стек
- Django 6.0.3, Python 3.14-slim, gunicorn
- PostgreSQL 14, Redis 7 (кэш db 1 + celery broker db 3)
- Celery worker без beat
- OSRM backend (OSM-данные по Санкт-Петербургу и ЛО), OR-Tools (VRP-солвер)
- MSApi (API МойСклада), Yandex Maps v3, Яндекс.Геокодер
- django-colorful, ratelimit, django_extra_views, widget_tweaks, pandas, pydantic

### Рантайм и Docker
- Код: site/ монтируется в /app; правки на хосте видны контейнеру сразу.
- Все Django-команды выполнять в основном контейнере web:

        docker compose exec web python manage.py <command>

- Базовые команды стека: docker compose up -d, docker compose down.
- Сервисы: db (snmprogs_db), redis (snmprogs_redis), web (snmprogs_web), celery (snmprogs_celery), osrm (snmprogs_osrm).
- OSRM-контейнер при первом старте сам строит граф, если map.osrm отсутствует.

## 2. Окружение
- .env в корне (не коммитится, шаблона нет).
- Критичные переменные: DB_NAME/DB_USER/DB_PASSWORD, REDIS_HOST, OSRM_URL, YANDEX_MAPS_API_KEY, EMAIL_*.
- Настройки: единый файл site/snmprogs/settings.py (+ common_settings.py), разделения dev/production нет.
- DJANGO_SERVER_TYPE (runserver/gunicorn/celery) определяет режим entrypoint.sh контейнеров web и celery.

## 3. Документация
- Документация проекта находится в docs/.
- Файлы в docs/plans/ не редактируй и не удаляй: это история изменений и планов.
- Перед изучением кода сначала ищи в docs/ информацию о задаче, планы и соглашения.
- Если нужной документации нет, фиксируй находки и напиши документацию по факту.
- Документация (кроме docs/plans/) описывает только фактическое состояние репозитория, без исторических оговорок вида "больше нет", "раньше", "теперь": история хранится в docs/plans/.
- Документация отражает только бизнес-логику и непосредственно связанные с ней общие моменты в коде (контракты данных, точки входа правил); механика реализации (MRO, kwargs, matching, устройство виджетов/JS-событий) в доки не выносится.
- Документация указывает ключевые классы и файлы правил, чтобы было понятно, куда смотреть в коде.

## 4. Планирование
- Новые планы только добавляются новыми файлами: после согласования и до реализации записывай план в docs/plans/<YYYYMMDD>_<formulated plan name>.md.
- Имя файла формулируй по смыслу задачи; дата указывается в формате YYYYMMDD.
- В любой план обязательно включай пункт "Актуализация документации": обнови docs по теме, а если документации по этой теме нет - напиши её.

## 5. Карта проекта
- Приложения (site/):
  - root - SingletonModelMixin (база singleton-настроек), индексная страница, динамический роутинг приложений по label; CacheMixin (uuid cache_key в redis).
  - moy_sklad_settings - MoySkladSettings (get_moy_sklad_token()), BlacklistProjectMS.
  - yandex_geocoder - Location: кэш адрес→координаты; сначала БД, при промахе Yandex API.
  - accounts_synchronize - синхронизация аккаунтов из МС (celery-задача).
  - demand_creator - создание отгрузок в МС для заказов с deliveryPlannedMoment на дату.
  - processing_creator - создание техопераций в МС по заказам на производство.
  - delivery_map_creator / delivery_map_loader - генерация / загрузка карт доставки (+ палитра).
  - delivery_distributor - экспериментальный роутинг курьеров: OR-Tools VRP + OSRM; Courier, DeliveryRoutingSettings.
  - courier_data_loader - обновление заказов в МС (проект + номер заказа).
  - yandex_map - template-tag для Yandex Maps JS.
  - paymentin_creator - создание оплат в МС (celery-задача).
  - celery_email - email-backend через celery (CeleryEmailBackend → send_messages_task).
- Библиотеки (не приложения): moy_sklad/ - MoySkladClient (token bucket, ретраи 429/5xx), creators/getters/updaters; moy_sklad_utils/ - пользовательские справочники МС и фильтры; map_constructor_model/ - pydantic-модели GeoJSON.
- Ядро солвера (delivery_distributor/core/): data_structure.py (pydantic-входные данные), delivery_data_preparator.py (точки + матрицы через OSRM), osrm_client.py (HTTP к OSRM), solver.py (OR-Tools: time/fuel/capacity/order dimensions), solution_processor.py (разбор решения, экспорт GeoJSON), time_intervals_identifier.py (парсинг временных окон доставки).
- URL-роутинг: /admin/, /accounts/, каждое приложение на своём label (root/urls.py динамически включает приложения); media через static().
- Шаблоны (site/templates/): base_generic.html (база), index.html (главная со списком приложений), auth-шаблоны, scripts_management (CRUD скриптов), utils/report_page.html.
- Celery-задачи: solve_vrp_task (delivery_distributor), create_paymentin_task (paymentin_creator), accounts_synchronize_task (accounts_synchronize), send_messages_task (celery_email).
- cache_key-паттерн: uuid в URL → dict в redis (TTL 3 часа): orders/couriers/settings/results/task_id; ProcessView опрашивает AsyncResult.
- OSRM: osrm/ полностью gitignored; pbf скачивается download_osrm_data.sh (geofabrik, СЗФО).
- Бизнес-логика: МС → demand_creator/processing_creator (отгрузки/техоперации) → delivery_distributor (VRP-маршруты) → GeoJSON на Yandex Maps; paymentin/accounts - синхронизация с МС.

## 6. Правила проекта
- .env не коммитится; токен МойСклада хранится в БД (MoySkladSettings), не в коде и не в git.

## 7. Миграции
- Миграция должна быть корректна для любого допустимого состояния БД, не под снимок.
- Историческая модель: только конкретный класс.
- RunPython: empty migration; модели через apps.get_model(); elidable=True; atomic=False при >1000 строк.

## 8. Тестирование и проверка
После миграции или изменения моделей, строго по порядку:
1. docker compose exec web python manage.py check
2. docker compose exec web python manage.py makemigrations --check --dry-run
3. docker compose exec web python manage.py migrate
4. docker compose exec web pytest <app> -v --reuse-db --nomigrations
5. docker compose exec web ruff check <app>

Дополнительно: линт по site/pyproject.toml, line-length 121.

## 9. Эскалация
- Escalation только для docker compose exec web ...
- pytest/ruff требуют escalation для запуска.
- Не объединяй разнородные команды в одном вызове.
- justification - под конкретную команду.
- Если отклонено - предложи выполнить самому, не обходи через psql/shell/установку на хост.

## 10. Делегирование субагентам
1. Дроби на атомарные срезы: один модуль плюс тест.
2. Сразу запрещай анализ домена, реализуй только по спецификации.
3. Давай готовый контракт и точные пути.
4. Скоуп: "только эти файлы" и "не трогай".
5. Краткий отчет по пунктам, без рассуждений о домене.
6. Сначала сам зафиксируй факты по коду.
7. Частные фактологические вопросы о сторонних библиотеках, фреймворках, документации и сети — делегируй субагенту `researcher` (инструмент `subagent`), не ищи сам.
