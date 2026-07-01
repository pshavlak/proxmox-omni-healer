---
title: Wiki Schema
created: 2026-05-26
updated: 2026-06-25
type: concept
tags: [архитектура, wiki]
---

# Wiki Schema

## Domain
Сайт села Золотаревка — неофициальный портал. **FastAPI-приложение** с динамическими страницами,
блочным редактором, SQLite, админ-панелью SPA, Jinja2-шаблонами и REST API.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `school-section.md`)
- Every wiki page starts with YAML frontmatter
- Use `[[wikilinks]]` to link between pages
- Bump `updated` date on every edit
- Every action appended to `log.md`

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
tags: [from taxonomy below]
sources: []
---
```

## Tag Taxonomy
- Разделы: школа, детсад, совхоз, спорт, жизнь-села, медиа, новости
- Технологии: fastapi, python, sqlite, jinja2, pydantic, uvicorn, nginx, proxmox, lxc
- Архитектура: админка, блоки, api, pages, roles, settings, media, suggestions, database
- Инфраструктура: server, ssh, deploy, ssl, deploy
- Статус: done, wip, planned, legacy

## Pages
- Entities: разделы сайта (школа, детсад, совхоз, спорт, жизнь-села, медиа, новости)
- Concepts: [[fastapi-architecture]], технические решения (блочный редактор, роли, медиа, загрузка)
- Legacy: [[admin-panel-redesign]] — старая WordPress админ-панель (archived)
- Comparisons: сравнения архитектурных решений
- Queries: результаты проверок и аудитов
