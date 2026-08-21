# Project Overview

Hysteria2 is a backup and maintenance bundle for a cascade VPN.

## Purpose

- Restore and maintain Hysteria 2 service for `hist.yupiterpro.ru`.
- Manage users through a small Flask panel and CLI script.
- Route traffic through a cascade SOCKS/Xray/WireProxy server.

## Repository Shape

- `config/` - Hysteria config, ACL, users database backup.
- `manager/` - Flask HTTP auth endpoint and web user panel.
- `nginx/` - public HTTPS config and hidden proxy path to manager.
- `systemd/` - units for Hysteria and manager.
- `wiki/` - local maintained project knowledge base.

## Boundary

This is not a packaged app. There is no dependency lockfile, test suite, or deployment automation. Production changes are done by copying files to `/opt/hysteria-manager/` and restarting `hysteria-manager`.
