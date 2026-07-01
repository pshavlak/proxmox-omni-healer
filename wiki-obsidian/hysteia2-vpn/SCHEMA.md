# Wiki Schema

## Domain

**Hysteria 2 VPN Infrastructure** — развёртывание, конфигурация, управление и мониторинг Hysteria 2 VPN сервера с каскадным SOCKS5-проксированием. Серверная инфраструктура включает Hysteria 2 (основной протокол), Xray (VLESS+REALITY), WireProxy (WireGuard+WARP), веб-панель управления (Flask), nginx (reverse proxy), ACL-маршрутизацию для разделения российского и иностранного трафика.

Серверы: основной Hysteria 2 сервер (62.113.105.38) и каскадный SOCKS5 сервер (193.164.155.153, Хельсинки). 19 пользователей VPN.

## Conventions

- File names: lowercase, hyphens, no spaces (e.g., `hysteria-2-protocol.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages that synthesise 3+ sources, append `^[raw/articles/source-file.md]` at the end of paragraphs whose claims come from a specific source.

## Frontmatter

```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

`confidence` and `contested` are optional — recommended for opinion-heavy or fast-moving topics.

### raw/ Frontmatter

```yaml
---
source_url: https://example.com/article
ingested: YYYY-MM-DD
sha256: <hex digest of the raw content below the frontmatter>
---
```

## Tag Taxonomy

- **Инфраструктура:** сервер, хостинг, сеть, архитектура, vps
- **Протоколы:** hysteria-2, quic, socks5, tls, vless, reality, wireguard, http3
- **Компоненты:** hysteria, xray, wireproxy, nginx, flask, systemd, certbot, fail2ban, crowdsec
- **Маршрутизация:** acl, geoip, geosite, каскад, прокси, direct
- **Операции:** управление, мониторинг, бэкап, восстановление, деплой, логи, cron
- **Безопасность:** ssh, аутентификация, сертификаты, firewall, пароли
- **Люди:** пользователь, администратор, клиент

Rule: every tag on a page must appear in this taxonomy. If a new tag is needed, add it here first, then use it.

## Page Thresholds

- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions, minor details, or things outside the domain
- **Split a page** when it exceeds ~200 lines — break into sub-topics with cross-links
- **Archive a page** when its content is fully superseded — move to `_archive/`, remove from index

## Entity Pages

One page per notable entity:

- **Серверы:** основной Hysteria 2 сервер, каскадный SOCKS5 сервер
- **Компоненты:** Hysteria 2, Xray, WireProxy, nginx, Flask-панель
- **Домены:** hist.yupiterpro.ru

Include: overview, key facts (IP, порты, версии), relationships, configuration highlights, source references.

## Concept Pages

One page per concept or topic:

- **Протоколы и технологии:** Hysteria 2, SOCKS5 каскад, ACL-маршрутизация, WireGuard+WARP
- **Архитектура:** общая схема прохождения трафика, инфраструктура
- **Управление:** пользователи, веб-панель, CLI, мониторинг
- **Известные проблемы:** утечка памяти WireProxy

Include: definition, current state, related concepts, open issues.

## Comparison Pages

Side-by-side analyses of different approaches or configurations (e.g., single-server vs cascade, direct vs SOCKS5 outbound).

## Update Policy

When new information conflicts with existing content:
1. Check the dates — newer sources generally supersede older ones
2. If genuinely contradictory, note both positions with dates and sources
3. Mark the contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in the lint report
