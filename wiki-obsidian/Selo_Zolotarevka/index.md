# Index — Сайт села Золотаревка

## Проект
- [[ТЕХНИЧЕСКОЕ_ЗАДАНИЕ_САЙТ_СЕЛА|Техническое задание]] — цели, структура разделов, требования к дизайну, этапы разработки. CMS: WordPress. 8 этапов, 2-3 недели.
- [[WORDPRESS_MVP_ARCHITECTURE_RESEARCH|WordPress MVP архитектура]] — техстек (WP 6.x, PHP 8.2+, MariaDB), плагины, план внедрения 2 недели. Рекомендация: контент-модель в коде (mu-plugin).
- [[BACKEND_PLAN|План бэкенда]] — реализация mu-plugin: CPT, роли, премодерация, REST API. Артефакты: `zolotarevka-backend.php`.
- [[DATA_MODEL|Модель данных]] — 8 CPT, 2 таксономии, статусы модерации, REST endpoint `zolo/v1/content/{type}`.
- [[IMPLEMENTATION_NOTES|Заметки по реализации]] — что реализовано в mu-plugin, что осталось на следующий этап.
- [[ROLE_MATRIX|Матрица ролей]] — 6 ролей P0: `administrator`, `school_editor`, `sports_editor`, `farm_editor`, `content_moderator`, `community_author`.

## Сценарии и UX
- [[SCENARIO_MVP_NARRATIVE_FLOW|MVP сценарии]] — 4 пользовательских сценария (житель, родитель, болельщик, автор UGC). Narrative flow: привлечение → выбор → ценность → вовлечение.
- [[PAGE_BLOCK_COPY|Блоки страниц и копирайтинг]] — все тексты для 7 страниц (главная, школа, детсад, совхоз, спорт, жизнь села, медиа). Hero, CTA, секционные заголовки.
- [[FORMS_COPY_AND_RULES|Формы: текст и правила]] — форма UGC «Предложить новость»: поля, валидация, модерационные статусы, антиспам.

## Контент
- [[CONTENT_PACK_P0|Пак контента P0]] — редакционная рамка, 7 контентных вертикалей, минимальный набор стартовых материалов, контентный календарь на 4 недели, CTA-блоки.
- [[CONTENT_HANDOFF|Передача контента]] — контракт между контентом, фронтендом и бэкендом: сущности, поля, порядок блоков на главной.

## Безопасность
- [[SECURITY_REVIEW|Security review]] — аудит кода: 0 critical, 0 high, 3 medium, 3 low. Проблемы: capability-mapping, отсутствие антиспама, нет лимитов payload.
- [[VULNERABILITY_LIST|Список уязвимостей]] — 6 findings с CWE. Medium: роль-модель, антиспам, лимиты. Low: error disclosure, comment_moderation, REST permission.
- [[FINAL_RISK_SIGNOFF|Финальный риск-сигнофф]] — conditional sign-off для P0 MVP. Medium residual risk. Запрещён масштабный запуск без Priority 0 фиксов.
- [[REMEDIATION_PLAN|План исправлений]] — Priority 0: capability mapping + антиспам. Priority 1-2: лимиты, error handling, REST hardening.
- [[HANDOFF_FRONTEND_SECURITY|Передача: фронтенд + безопасность]] — endpoint'ы для фронта, P0 защита формы, P0 защита комментариев, ограничения.

## Задачи
- [[SEO_TASK|SEO: предоставить ссылку на запущенный сайт]] — задача для SEO-специалиста, заблокирована этапом 8 (запуск).

## Тестирование
- [[TEST_CHECKLIST|Чеклист тестирования]] — smoke, роли, модерация, REST, безопасность. 8 пунктов.

## Код
- `site/` — HTML/CSS/JS прототип фронтенда. Страницы: главная, школа, детсад, спорт, совхоз, жизнь села, медиа, новости.
- `wordpress/` — WordPress mu-plugins (`zolotarevka-backend.php`) и тема `zolotarevka-mvp` (шаблоны разделов).
- **Админ-панель контента** — `Zolotarevka_MVP_Settings` в mu-plugin (1942 строки). Топ-меню "Золотаревка ⚙️", редакторы 8 страниц, настройки сайта, навигация через WP Menus. Публикация через двухключевой паттерн (draft/live) с предпросмотром.
- Календарь и результаты — postmeta `calendar_data` в CPT `sports_season`. Админ: `css/admin-calendar.css`, `js/admin-calendar.js`.
- Турнирная таблица — postmeta `standings_data` (ЗМ/ПМ/±, очки 3-1-0). Авторасчёт из результатов.

## Инфраструктура
- [[SERVER_INFRASTRUCTURE|Серверная инфраструктура]] — текущая архитектура: новый сервер (31.56.208.248), LXC-контейнер на Proxmox, FastAPI + SQLite, reverse SSH tunnel, Cloudflare DNS, ожидание SSL.

## Paperclip (LLM-агенты)
- [[PAPPERCLIP_API_KEYS|API ключи Paperclip/Codex]] — где и как менять API ключ DeepSeek в Paperclip, `.env`, `auth.json`, `config.toml`, `adapterConfig` агентов.

## Вводные
- [[Добро_пожаловать|Добро пожаловать]] — точка входа в wiki
- [[log|Log изменений]] — история правок
- `sources/` — исходные документы (read-only)
