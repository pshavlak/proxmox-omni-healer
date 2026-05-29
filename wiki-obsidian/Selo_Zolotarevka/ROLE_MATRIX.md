# ROLE_MATRIX

## Базовые роли
- `administrator`: полный контроль WordPress.
- `school_editor`: управление школьным разделом, публикация, модерация комментариев.
- `sports_editor`: управление спортивным разделом, публикация, модерация комментариев.
- `farm_editor`: управление контентом совхоза, публикация, модерация комментариев.
- `content_moderator`: ручная премодерация комментариев и пользовательских подач.
- `community_author`: создание собственных материалов без мгновенной публикации.

## P0 capability-сетка
- Публикация: domain editor + administrator.
- Модерация комментариев: moderator + domain editors + administrator.
- Управление ролями/пользователями: administrator.
- Пользовательская подача через форму: все (включая неавторизованных), но только в `pending`.

---
**Связанные страницы:** [[ТЕХНИЧЕСКОЕ_ЗАДАНИЕ_САЙТ_СЕЛА|ТЗ]], [[BACKEND_PLAN|План бэкенда]], [[SECURITY_REVIEW|Security review]], [[HANDOFF_FRONTEND_SECURITY|Передача фронтенд+security]], [[FORMS_COPY_AND_RULES|Формы]]
