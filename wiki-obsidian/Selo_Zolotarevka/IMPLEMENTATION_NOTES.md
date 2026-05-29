# IMPLEMENTATION_NOTES

## Локация кода
- `wordpress/mu-plugins/zolotarevka-backend.php`

## Что реализовано
- Регистрация 8 CPT и 2 таксономий через `register_post_type` / `register_taxonomy`.
- Регистрация ролей P0: `school_editor`, `sports_editor`, `farm_editor`, `content_moderator`, `community_author`.
- Принудительная премодерация комментариев через `update_option`.
- Обработчик формы `admin-post`: action `zolo_submit_news`.
- REST endpoint для фронтенда: `zolo/v1/content/{type}`.

## Подключение формы на фронте
- Форму направить на `POST /wp-admin/admin-post.php`.
- Добавить hidden-поля:
  - `action=zolo_submit_news`
  - `_wpnonce` из `wp_nonce_field('zolo_submit_news')`
  - `news_title`
  - `news_text`

## Что оставлено на следующий этап
- Anti-spam: captcha/honeypot/rate limit.
- Тонкая настройка capability по каждому CPT через `capability_type`/`capabilities`.
- Расширенный REST payload с медиа, tax terms и пользовательскими полями.

---
**Связанные страницы:** [[BACKEND_PLAN|План бэкенда]], [[DATA_MODEL|Модель данных]], [[HANDOFF_FRONTEND_SECURITY|Передача фронтенд+security]], [[TEST_CHECKLIST|Чеклист тестирования]]
