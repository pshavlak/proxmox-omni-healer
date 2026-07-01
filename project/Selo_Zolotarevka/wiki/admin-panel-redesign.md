---
title: Админ-панель — WordPress версия (legacy)
created: 2026-06-09
updated: 2026-06-25
type: concept
tags: [архитектура, админка, редизайн, блоки, роли, legacy]
sources: [sketches/DIALOG_REDESIGN_2026-06-09.md, sketches/site-builder-v2.html]
status: legacy
---

> ⚠️ **LEGACY** — эта админ-панель заменена новой **FastAPI + SPA админ-панелью**.
> См. [[fastapi-architecture]] для актуальной архитектуры.
> WordPress-версия остаётся на сервере `wordpress-vm` (192.168.1.64) для истории,
> но весь новый функционал разрабатывается на новом стеке.

# Админ-панель — единый каталог управления

## Текущий статус
✅ **Реализовано и задеплоено** на https://zolotarevka.yupiterpro.ru/wp-admin/admin.php?page=zolotarevka-v2

## Архитектура

Вся админ-панель — одно SPA-приложение на jQuery. Левая колонка — навигация, правая — редактор.

### Навигация (левая колонка)

| Кнопка | Раздел | Функционал |
|--------|--------|-----------|
| 🗺️ Страницы сайта | Дерево страниц + блочный редактор | Разделы/подразделы, блоки (10 типов), draft/live |
| 🖼️ Медиа-центр | Управление видео и галереей | Добавление/удаление видео Rutube/VK inline |
| 📰 Контент | Все CPT записи сайта | Таблицы со статусом, открытие в WP-редакторе |
| ⚙️ Настройки | Соцсети, контакты, текст | VK, Telegram, OK, RSS, Email, телефон, теглайн |
| 👥 Пользователи и роли | Роли с доступом к разделам | Статистика, редактирование, поиск |

### Динамические страницы

Разделы и подразделы создаются/удаляются из админки через модалки. Хранятся в опции `zolo_site_pages`.

```php
// Структура данных
update_option('zolo_site_pages', [
  ['id' => 'school', 'name' => 'Школа', 'icon' => '📚', 'parent' => '', 'order' => 0, 'status' => 'published'],
  ['id' => 'school-news', 'name' => 'Новости школы', 'icon' => '📰', 'parent' => 'school', 'order' => 0, 'status' => 'published'],
]);
```

### Блочный редактор

Каждая страница собирается из блоков. Блоки хранятся в `zolo_blocks_{page_id}_draft` и `zolo_blocks_{page_id}_live`.

**10 типов блоков:**
- 🧱 **Hero / Баннер** — заголовок, подзаголовок, фон (URL), CTA-кнопка
- 📝 **Текст** — HTML-текст (wp_kses_post)
- 🖼️ **Изображение** — URL + подпись + alt
- 📸 **Галерея** — сетка (количество колонок)
- 🎬 **Видео** — URL Rutube/VK + embed
- 📊 **Таблица** — заголовки + строки
- 🏗️ **Карточки / Плитки** — авто-режим из дерева или ручной
- 📄 **Документы** — список файлов
- 📋 **Форма** — обратная связь / предложить новость
- ➖ **Разделитель** — без настроек

```php
// Структура блока
update_option('zolo_blocks_home_draft', [
  ['id' => 'b1', 'type' => 'hero', 'name' => '🧱 Hero / Баннер', 'config' => [
    'title' => 'Добро пожаловать!', 'subtitle' => '', 'bg_image' => '', 'btn_text' => '', 'btn_url' => '',
  ]],
]);
```

### Роли

Роли привязаны к разделам сайта через чекбоксы. Хранятся в `zolo_roles_v2`.

```php
update_option('zolo_roles_v2', [
  ['id' => 'school_editor', 'name' => 'Редактор школы', 'icon' => '📚', 'sections' => ['school'], 'caps' => ['moderate_comments' => true, 'upload_files' => true]],
]);
```

### Совместимость

Все старые функции сохранены и работают:
- `zolo_get_page_content($slug)` — возвращает данные как раньше, синхронизируется через `zolo_publish_page`
- `zolo_get_site_settings()` — без изменений
- `zolo_has_draft_changes()` — работает
- Шаблоны темы (`front-page.php`, `page.php`, `template-parts/pages/*.php`) — **без изменений**

### Файлы

| Файл | Назначение |
|------|-----------|
| `wordpress/mu-plugins/zolotarevka-backend.php` | Главный плагин: CPT, роли, AJAX, REST, рендерер |
| `wordpress/mu-plugins/zolotarevka-admin.css` | Стили админ-панели |
| `wordpress/mu-plugins/zolotarevka-admin.js` | JS: дерево, блоки, модалки, медиа, контент, настройки |

### API (REST)

- `GET /wp-json/zolo/v1/content/{type}` — публичные записи (как было)
- `GET /wp-json/zolo/v2/page/{pid}/blocks` — опубликованные блоки страницы

### AJAX-эндпоинты

| Action | Описание |
|--------|----------|
| `zolo_get_data` | Все данные: страницы, роли, пользователи, видео, галерея, настройки, контент |
| `zolo_get_blocks` | Блоки страницы (draft) |
| `zolo_save_blocks` | Сохранить блоки (draft) |
| `zolo_publish_page` | Опубликовать страницу (draft → live + legacy sync) |
| `zolo_publish_all` | Опубликовать все |
| `zolo_save_page` | Создать/обновить страницу в дереве |
| `zolo_delete_page` | Удалить страницу и её блоки |
| `zolo_save_roles` | Сохранить все роли |
| `zolo_delete_role` | Удалить роль |
| `zolo_get_videos` / `zolo_save_video` / `zolo_delete_video` | CRUD видео |
| `zolo_get_gallery_items` / `zolo_save_gallery_item` / `zolo_delete_gallery_item` | CRUD галереи |
| `zolo_save_site_settings` | Сохранить настройки сайта |
| `zolo_get_recent_content` | Последние записи по всем CPT |
| `zolo_save_pages` | Сохранить всё дерево страниц (batch) |
