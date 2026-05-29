# HANDOFF_FRONTEND_SECURITY

## Для frontend
- Использовать endpoint: `GET /wp-json/zolo/v1/content/{type}`.
- Поддерживаемые `type`:
  - `school_news`, `kindergarten_news`, `farm_production`, `farm_vacancies`,
  - `sports_team`, `sports_match`, `bulletin_board`, `gallery`.
- Для формы "Предложить новость":
  - `POST /wp-admin/admin-post.php`
  - `action=zolo_submit_news`
  - обязательный nonce `zolo_submit_news`
  - поля `news_title`, `news_text`.

## Для security
- P0 защита формы:
  - CSRF: `wp_verify_nonce`.
  - Санитизация: `sanitize_text_field`, `wp_kses_post`.
  - Публикация только в `pending`.
- P0 защита комментариев:
  - `comment_moderation=1`
  - `comment_previously_approved=0`
- Ограничения P0:
  - нет captcha/rate-limit/honeypot;
  - capability-модель ролей базовая, нужна проверка на least privilege во время security sign-off.

---
**Связанные страницы:** [[BACKEND_PLAN|План бэкенда]], [[SECURITY_REVIEW|Security review]], [[VULNERABILITY_LIST|Уязвимости]], [[FORMS_COPY_AND_RULES|Формы]], [[IMPLEMENTATION_NOTES|Заметки по реализации]]
