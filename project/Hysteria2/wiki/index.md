# Index

## Overview

- [[pages/project-overview|Project Overview]] - назначение проекта, состав файлов, границы ответственности.
- [[pages/architecture|Architecture]] - схема каскадного VPN и фактические порты.
- [[pages/servers|Servers]] - основной и каскадный серверы, сервисы, проверки.
- [[pages/operations|Operations]] - безопасные команды проверки и деплоя.
- [[pages/security|Security]] - риски, секреты, исправления и правила обращения.
- [[pages/known-issues|Known Issues]] - текущие проблемы и наблюдения.
- [[pages/telegram-miniapp-plan|Telegram Mini App Plan]] - план кабинета клиента, подписок, ссылок и будущих оплат.
- [[pages/telegram-miniapp-server-rollout|Telegram Mini App Server Rollout]] - безопасный план переноса Mini App на сервер.

## Meta

- [[schema|Schema]] - правила поддержки wiki.
- [[log|Log]] - хронология изменений и проверок.
- [[raw/sources|Sources]] - внешние и локальные источники.

## Current Verified Facts

- Рабочий Hysteria endpoint: `hist.yupiterpro.ru:8443`.
- Публичный HTTPS/nginx endpoint: `https://hist.yupiterpro.ru` - заглушка для скрытия VPN.
- Админ-панель: `https://hist.yupiterpro.ru/44169d2dba4d0fd5/`.
- Manager: `127.0.0.1:8081` на основном сервере.
- Каскадный SOCKS endpoint: `193.164.155.153:18443`.
- Последняя проверка полного прохода: 2026-08-11, выходной IP `193.164.155.153`.
