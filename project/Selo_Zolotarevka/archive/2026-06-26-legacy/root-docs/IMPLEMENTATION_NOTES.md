# IMPLEMENTATION_NOTES

## Локация кода
- `wordpress/mu-plugins/zolotarevka-backend.php`
- `wordpress/themes/zolotarevka-mvp/`

## Что реализовано (базовое)
- Регистрация 8 CPT и 2 таксономий через `register_post_type` / `register_taxonomy`.
- Регистрация ролей P0: `school_editor`, `sports_editor`, `farm_editor`, `content_moderator`, `community_author`.
- Принудительная премодерация комментариев через `update_option`.
- Обработчик формы `admin-post`: action `zolo_submit_news`.
- REST endpoint для фронтенда: `zolo/v1/content/{type}`.

## Что реализовано (июнь 2026)

### Админ-панель «Золотаревка ⚙️»
- Кастомное меню с dashboard, настройками сайта и редактором каждой страницы
- Система черновиков/публикации контента (draft → live через опции WP)
- Настройки сайта: соцсети VK/Telegram/OK/RSS, контакты, теглайн

### Изображения на страницах
- Добавлено поле `hero_image` для главной (фон hero-секции)
- Добавлено поле `page_image` для всех страниц-разделов (фон page-header)
- Кнопка «📷 Выбрать» — выбор из медиатеки WordPress
- Кнопка «📤 Загрузить» — загрузка с компьютера/телефона
- Превью изображения после выбора
- Интеграция с медиатекой через wp.media JavaScript API

### Документы (PDF/DOC/XLS) на страницах
- Repeater-поля в редакторе каждой страницы-раздела
- Поля: название документа, ссылка на файл, описание
- Кнопка «📎 Выбрать» — выбор из медиатеки
- Кнопка «📤 Загрузить» — загрузка с компьютера
- Отображение на сайте: карточки с иконками по типу (📕 PDF, 📘 DOC, 📗 XLS)
- CSS-стили для .documents-section, .doc-card, .documents-grid

### Видео-блок
- CPT `zolo_video` с метабоксом для ссылки Rutube/VK Video
- REST API endpoint `/wp-json/wp/v2/videos` (исправлен: добавлен `rest_base`)
- 3 демо-записи добавлены через WP-CLI

### Прочее
- Создан отдельный SSH-ключ для WordPress VM (`~/.ssh/id_wordpress`)
- Добавлен алиас в SSH config: `wordpress-vm`
- Исправлен `rest_base` для zolo_video (был 404 в REST API)

## Подключение формы на фронте
- Форму направить на `POST /wp-admin/admin-post.php`.
- Добавить hidden-поля:
  - `action=zolo_submit_news`
  - `_wpnonce` из `wp_nonce_field('zolo_submit_news')`
  - `news_title`
  - `news_text`

## Что оставлено на следующий этап
- Anti-spam: captcha/honeypot/rate limit (базовый rate limit уже есть).
- Тонкая настройка capability по каждому CPT через `capability_type`/`capabilities`.
- Расширенный REST payload с медиа, tax terms и пользовательскими полями.
- Шаблон для страницы «Соц. обслуживание» (страница создана, шаблон через page.php по умолчанию).
