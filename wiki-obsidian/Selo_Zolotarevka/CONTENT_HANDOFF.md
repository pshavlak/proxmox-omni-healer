# CONTENT_HANDOFF

Дата: 2026-05-26  
Issue: YUP-5

## 1) Назначение документа

Документ фиксирует контракт между контентом, фронтендом и бэкендом для P0 WordPress MVP: какие сущности нужны, какие поля обязательны, и в каком формате они отображаются.

## 2) Сущности и поля P0

### 2.1 `post` (новости)
Обязательные поля:
- `post_title` (string, 6-120)
- `post_excerpt` (string, 80-320)
- `post_content` (string, 300-6000)
- `sector` (taxonomy, single)
- `featured_image` (image)
- `post_date` (datetime)

Опционально:
- `cta_label` (string, до 40)
- `cta_url` (url)

### 2.2 `sports_match`
Обязательные поля:
- `match_datetime` (datetime)
- `opponent` (string, 2-80)
- `is_home` (boolean)
- `status` (`upcoming`|`finished`)

Опционально:
- `score_our` (int, 0-99)
- `score_opponent` (int, 0-99)
- `goals_summary` (string, до 400)

### 2.3 `bulletin`
Обязательные поля:
- `title` (string, 6-120)
- `body` (string, 40-1500)
- `bulletin_type` (`buy`|`sell`|`service`)
- `contact` (string, 5-120)
- `expires_at` (date)

### 2.4 `farm_vacancy`
Обязательные поля:
- `title` (string, 6-120)
- `salary_note` (string, до 120)
- `description` (string, 80-3000)
- `contact` (string, 5-120)

### 2.5 `village_event`
Обязательные поля:
- `title` (string, 6-120)
- `event_date` (datetime)
- `location` (string, 2-120)
- `program_short` (string, 40-800)

## 3) Контракт отображения (Frontend)

### 3.1 Главная
Порядок блоков:
1. Hero
2. Быстрые разделы (6 карточек)
3. Ближайший матч (`sports_match` со статусом `upcoming`, ближайшая дата)
4. Последние новости (6 шт, `post`, сортировка по дате)
5. CTA "Предложить новость"

### 3.2 Страницы разделов
- H1 + лид из `PAGE_BLOCK_COPY.md`
- Лента материалов по соответствующему `sector`
- Пагинация по 9 карточек
- Нижний CTA блока раздела

### 3.3 Спорт
- Виджет ближайшего матча
- Последний завершенный матч
- Табличный блок (MVP вручную)
- Список 6 последних спортивных публикаций

## 4) Контракт обработки формы UGC (Backend)

Endpoint (пример): `/wp-json/zolotarevka/v1/ugc`

Payload:
- `name` string
- `contact` string
- `sector` enum
- `title` string
- `body` string
- `attachment` file (multipart, optional)
- `consent` boolean

Логика:
- валидировать по `FORMS_COPY_AND_RULES.md`;
- сохранять в отдельный тип `ugc_submission` или как `post` со статусом `pending`;
- назначать модератору уведомление;
- возвращать пользователю локализованный ответ успеха/ошибки.

## 5) Ограничения и форматы

- Часовой пояс публикаций: Europe/Moscow.
- Формат даты на фронте: `dd.mm.yyyy`.
- Кодировка: UTF-8.
- Все обязательные текстовые поля триммируются.
- Пустые строки после тримминга считаются отсутствующими.

## 6) Definition of Ready для интеграции

Контент-пакет считается готовым к внедрению, если:
- тексты блоков и CTA подключены без правок смысла;
- форма UGC отдает понятные ошибки валидации;
- минимум 20 стартовых сущностей контента импортированы в админку;
- на главной отображаются: hero, быстрые разделы, матч, новости, CTA;
- модератор может провести заявку по статусам `new -> in_review -> approved/rejected`.

---
**Связанные страницы:** [[CONTENT_PACK_P0|Контент P0]], [[PAGE_BLOCK_COPY|Копирайтинг]], [[FORMS_COPY_AND_RULES|Формы]], [[DATA_MODEL|Модель данных]], [[HANDOFF_FRONTEND_SECURITY|Передача фронтенд+security]]
