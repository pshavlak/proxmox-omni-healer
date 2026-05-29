# BACKEND_PLAN

## Цель
Реализовать P0 backend для WordPress MVP: модель данных, роли, премодерацию и API-слой для фронтенда.

## Шаги реализации
1. Создать `mu-plugin` с регистрацией CPT и таксономий.
2. Добавить роли и базовые capability-наборы для редакторов доменов и модератора.
3. Включить премодерацию комментариев через WP options.
4. Реализовать форму "Предложить новость" через `admin-post` с сохранением в `pending`.
5. Открыть REST endpoint `zolo/v1/content/{type}` для фронтенда.
6. Подготовить handoff-документацию для frontend/security.

## Артефакты
- `wordpress/mu-plugins/zolotarevka-backend.php`
- `DATA_MODEL.md`
- `ROLE_MATRIX.md`
- `IMPLEMENTATION_NOTES.md`
- `TEST_CHECKLIST.md`
- `HANDOFF_FRONTEND_SECURITY.md`

## Риски
- Ограниченные capability без кастомного `map_meta_cap` могут потребовать уточнения на UAT.
- `update_option` в `init` для модерации комментариев может переопределять ручные настройки админа.
- Форма без anti-spam слоя (captcha/rate-limit) закрывает только P0.

---
**Связанные страницы:** [[ТЕХНИЧЕСКОЕ_ЗАДАНИЕ_САЙТ_СЕЛА|ТЗ]], [[DATA_MODEL|Модель данных]], [[ROLE_MATRIX|Роли]], [[IMPLEMENTATION_NOTES|Заметки по реализации]], [[HANDOFF_FRONTEND_SECURITY|Передача фронтенд+security]]

## Критерии завершения
- CPT/таксономии доступны в админке и REST.
- Форма отправляет данные в `pending` и не публикует напрямую.
- Комментарии идут в премодерацию.
- Документы для frontend/security готовы.
