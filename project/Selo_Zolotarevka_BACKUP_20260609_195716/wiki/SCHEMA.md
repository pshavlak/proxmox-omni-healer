---
title: Wiki Schema
created: 2026-05-26
updated: 2026-06-09
type: concept
tags: [архитектура, wiki]
---

# Wiki Schema

## Domain
Сайт села Золотаревка — неофициальный портал. WordPress-сайт с кастомной темой, CPT, REST API.

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
- Технологии: wordpress, php, mysql, nginx, proxmox, lxc
- Архитектура: cpt, taxonomy, roles, rest-api, theme, mu-plugin, админка, блоки, редизайн
- Инфраструктура: server, ssh, deploy, ssl
- Статус: done, wip, planned

## Pages
- Entities: разделы сайта (школа, детсад, совхоз, спорт, жизнь-села, медиа, новости)
- Concepts: технические решения (CPT, роли, видео-блок, документы, загрузка медиа, [[admin-panel-redesign]])
- Comparisons: сравнения архитектурных решений
- Queries: результаты проверок и аудитов
