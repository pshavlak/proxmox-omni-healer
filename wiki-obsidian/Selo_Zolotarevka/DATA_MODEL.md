# DATA_MODEL

## CPT
- `school_news`: новости школы.
- `kindergarten_news`: новости детского сада.
- `farm_production`: карточки продукции совхоза.
- `farm_vacancies`: вакансии совхоза.
- `sports_team`: команды и составы.
- `sports_match`: матчи/результаты.
- `bulletin_board`: объявления и пользовательские подачи.
- `gallery`: элементы фотогалереи.

## Таксономии
- `content_section` (hierarchical): общий классификатор разделов.
- `sports_kind` (hierarchical): виды спорта для `sports_team` и `sports_match`.

## Статусы модерации
- Публикация формы "Предложить новость" создается как `pending` в `bulletin_board`.
- Источник записи: meta `_zolo_submission_source=form_submit_news`.

## REST данные для фронтенда
Endpoint: `GET /wp-json/zolo/v1/content/{type}?per_page=10`

Формат:
- `type`: строка.
- `count`: число.
- `items[]`: `{ id, title, excerpt, date, link }`.

---
**Связанные страницы:** [[ТЕХНИЧЕСКОЕ_ЗАДАНИЕ_САЙТ_СЕЛА|ТЗ]], [[BACKEND_PLAN|План бэкенда]], [[WORDPRESS_MVP_ARCHITECTURE_RESEARCH|Архитектура WP]], [[CONTENT_HANDOFF|Передача контента]]
