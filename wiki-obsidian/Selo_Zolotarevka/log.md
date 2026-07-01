# Log изменений

## [2026-06-02] feat | Админ-панель управления контентом + деплой
- Добавлен класс `Zolotarevka_MVP_Settings` в mu-plugin: топ-меню "Золотаревка ⚙️" с 10 подменю
- Панель управления: статус страниц, кнопка "Опубликовать всё", быстрые ссылки
- Настройки сайта: соцсети, контакты, теглайн, копирайт — через Settings API
- Редакторы 8 страниц: hero, bento, school, kindergarten, farm, sports, village-life, media, news
- Публикация с двухключевым паттерном (черновик/опубликовано) + предпросмотр
- Навигация через WP Menus (`register_nav_menus`) с fallback на `zolo_nav_items()`
- Футер динамический из `zolo_site_settings` (колонки, ссылки, копирайт)
- Все шаблоны читают контент из опций, preview-режим с жёлтой плашкой
- Capability `zolo_edit_site_content` для админа + редакторов разделов
- Задеплоено на сервер, бэкап: `/var/www/html/wordpress/wp-content/backup-20260602_164733/`
- Исправлен IP в .env и документации: 192.168.1.65 → 192.168.1.64

## [2026-05-31] feat | Состав команды в админке + удалён блок «Прошедший матч»
- Удалён блок «Прошедший матч» (с заголовком, датой и авторами голов) со страницы Спорт
- Добавлен метабокс «Состав команды» для `sports_team`: поля Номер, Возраст, Амплуа
- Амплуа сохраняется в excerpt (обратная совместимость с фронтендом)
- В `sports.php` убран лишний WP_Query на `sports_match` + HTML-блок

## [2026-05-30] feat | Редактирование турнирной таблицы через админку
- Создан CPT `sports_season` (Сезоны) для хранения турнирных таблиц по годам
- Добавлен метабокс "Турнирная таблица" с динамическим редактором строк (команда, И, В, Н, П, О)
- Данные хранятся в postmeta `standings_data` (сериализованный массив)
- Заменена жёстко зашитая таблица в `template-parts/pages/sports.php` на динамический цикл WP_Query
- Все сезоны показываются на странице Спорт, сортировка DESC (новый сверху), первая строка подсвечена
- Добавлены REST endpoint'ы: `GET /zolo/v1/standings` (список) и `GET /zolo/v1/standings/{id}` (с таблицей)
- Роль `sports_editor` расширена на `sports_season`

## [2026-05-28] setup | Инициализация LLM Wiki
- Создана структура LLM Wiki (CLAUDE.md, sources/, index.md, log.md)
- Добавлен каталог страниц (index.md)

## [2026-05-29] task | SEO: ссылка на запущенный сайт
- Создана [[SEO_TASK]] — задача для SEO-специалиста, заблокирована этапом 8
- Обновлён index.md (добавлен раздел "Задачи")

## [2026-05-29] deploy | Перенос локального сайта на WordPress
- Конвертированы все 8 шаблонов: жёсткий контент → WP_Query из CPT
- Исправлен main.js: удалены обработчики форм, блокировавшие POST (suggestForm, commentForm)
- Развёрнуты на сервере: mu-plugin (zolotarevka-backend) и тема (zolotarevka-mvp)
- Активирован mod_rewrite, настроены permalinks (%postname%)
- Удалены старые плагины (WooCommerce, real-estate, ratings) и тема (aster-real-estate)
- Созданы 7 страниц (school, kindergarten, farm, sports, village-life, media, news)
- Загружен демо-контент: 43 записи во все 8 CPT
- Форма "Предложить новость" работает: POST → admin-post → pending с nonce/honeypot/rate-limit
- Все страницы доступны: http://192.168.1.64/

## [2026-05-29] ops | Диагностика и фикс WordPress сервера
- Подключение к LXC-контейнеру `root@192.168.1.64`
- Выявлена проблема: siteurl/home указывали на 192.168.1.65 вместо 192.168.1.64 — причина тормозов
- Исправлено: обновлены siteurl и home в БД WordPress
- Создана [[SERVER_INFRASTRUCTURE]] — страница с описанием стека, конфигурации и известных проблем

## [2026-05-30] ops | Оптимизация WordPress сервера (site health)
- Выполнена диагностика site health; удалены неактивные темы (`twentytwentythree`, `twentytwentyfour`)
- Установлен PHP модуль imagick
- Настроен Redis (v8.0.2) + php8.4-redis + Redis Object Cache plugin — persistent object cache активен
- Почищен хлам: удалены 5 остаточных cron-задач (Jetpack, WooCommerce, kk-star-ratings), файлы WooCommerce, DB options
- Исправлен MariaDB репозиторий, обновлён GPG-ключ Sury PHP repo
|- Обновлена [[SERVER_INFRASTRUCTURE]] — стек, плагины, темы, Redis, OPcache
|
|## [2026-07-01] ops | Обновление серверной инфраструктуры — переезд с Beget VPS
|- Сайт перенесён со старой VPS (62.113.105.38, Beget) на новый сервер (31.56.208.248)
|- Обновлён [[SERVER_INFRASTRUCTURE]] — новая архитектура: новый сервер + LXC + reverse SSH tunnel + Cloudflare DNS
|- Обновлён index.md — описание инфраструктуры
|- Обновлён [[SEO_TASK]] — удалены ссылки на старый VPS домен (zolotarevka.yupiterpro.ru)
|- Текущий статус: DNS на Cloudflare, NS propagation в процессе, SSL не получен, SSH на новый сервер заблокирован UFW
|
|## [2026-07-01] ops | Настройка сервера, SSL, запуск сайта
|- Подключен SSH к серверу 31.56.208.248 (ключ id_31_56_208_248)
|- Запущен reverse tunnel LXC → сервер (systemctl start reverse-tunnel)
|- Получен SSL сертификат Let's Encrypt через certbot для xn--80aaflivdxbvu.xn--p1ai (золатаревка.рф) — истекает 2026-09-29
|- Настроен HTTP → HTTPS редирект
|- Удалён крон zolotarevka-ssl (certbot автообновление вместо acme.sh)
|- Сайт доступен по https://золотаревка.рф (через Cloudflare proxy)
## [2026-05-30] deploy | Вывод сайта в интернет (золотаревка.рф)
- Настроен WireGuard туннель VPS (62.113.105.38) ↔ LXC (192.168.1.64), 10.0.0.0/24
- Настроен nginx reverse proxy на VPS для zolotarevka.yupiterpro.ru (временный домен)
- Получен SSL Let's Encrypt для zolotarevka.yupiterpro.ru (истекает 2026-08-28)
- Включён UFW фаервол на VPS (только SSH, HTTP, HTTPS, WG, Hysteria2)
- Настроен unattended-upgrades на VPS
- PHP hardening на LXC: disable_functions, allow_url_fopen=Off, expose_php=Off
- wp-config.php hardening: DISALLOW_FILE_EDIT, WP_AUTO_UPDATE_CORE, FORCE_SSL_ADMIN
- Заблокирован xmlrpc.php, rate limit на wp-login и REST API
- server_tokens off глобально на nginx
- Hysteria2 VPN не затронут (UDP 8443, не пересекается с nginx)
- Обновлена [[SERVER_INFRASTRUCTURE]]

## [2026-05-30] fix | Mixed content за reverse proxy
- Исправлена генерация URL в WordPress за nginx reverse proxy
- Причина: WordPress не знал о HTTPS (nginx → Apache по HTTP), генерировал `http://` ссылки
- Redis кэш хранил старые ссылки на `http://192.168.1.64` — очищен
- Добавлен detection `X-Forwarded-Proto: https` в wp-config.php для корректного определения протокола
- Проверено: все ресурсы (CSS, JS, ссылки) грузятся по HTTPS

## [2026-05-30] ops | Документация замены API ключей Paperclip
- Создана [[PAPPERCLIP_API_KEYS]] — 5 мест где нужно менять ключ DeepSeek
- Обновлён index.md (добавлен раздел "Paperclip (LLM-агенты)")
- Ключ заменён в: `.env`, `auth.json`, `config.toml` (x2), `adapterConfig` CEO агента

## [2026-05-28] ingest | Полная индексация wiki
- Прочитаны все 17 страниц wiki
- Обновлён index.md с детальными описаниями каждой страницы
- Проставлены [[вики-ссылки]] между всеми связанными страницами
- Категоризация: Проект, Сценарии/UX, Контент, Безопасность, Тестирование, Код

## [2026-05-30] feat | Календарь + результаты + турнирная таблица (12 команд)
- Распознан файл `1круг.jpg`: 12 команд, 4 тура (24 матча) первого круга
- Расширена турнирная таблица: добавлены колонки ЗМ/ПМ/±, очки (3-1-0)
- Создан метабокс «Календарь и результаты» для `sports_season` с:
  - Редактором по кругам (1 круг / 2 круг)
  - Редактором по турам (добавление/удаление туров и матчей)
  - Полями: хозяева, гости, счёт, статус (запланирован/сыгран/перенесён)
- Кнопка «Авторассчитать турнирную таблицу из результатов» (AJAX)
- Кнопка «Авторассчитать» в JS на форме (мгновенный расчёт без сохранения)
- REST API: `GET /zolo/v1/calendar/{id}`
- Вспомогательные методы: `get_calendar_for_display()`, `get_standings_for_display()`
- Фронтенд `sports.php`: календарь по кругам/турам, расширенная таблица, блок результатов
- Создан сезон «Чемпионат 2026» (ID: 88) с полным календарём 1+2 круга (48 матчей) и 12 командами
- Админские ассеты: `css/admin-calendar.css`, `js/admin-calendar.js`
- Данные импортированы из `1круг.jpg` через OCR (macOS Vision)

## [2026-05-31] fix | Названия команд в одну строку (календарь, результаты, таблица)
- В календаре (таблица) добавлен `white-space:nowrap` — названия команд не переносятся
- В результатах (сетка 2 колонки) добавлен `white-space:nowrap` — длинные названия не вылезают
- В турнирной таблице добавлен `white-space:nowrap` — название команды всегда в строку
- Убрано `overflow:hidden` + `text-overflow:ellipsis` — названия не обрезаются, таблица скроллится

## [2026-05-31] fix | Отображение счёта inline + номер тура
- Счёт выводится в одной строке между командами (вместо отдельной колонки)
- Добавлено поле `round` в форму календаря — номер тура теперь сохраняется явно
- Исправлено отображение номера тура на фронтенде
