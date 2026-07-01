# 🛡️ Outline VPN сервер

**Сервер:** `95.182.98.178` (`paris`)
**Статус:** ✅ Работает

---

## 📊 Состояние

| Компонент | Статус | Аптайм |
|-----------|--------|--------|
| **shadowbox** (VPN) | ✅ Up | 2 часа |
| **watchtower** (автообновление) | ✅ Healthy | 2 часа |
| **outline-ss-server** (Shadowsocks) | ✅ Работает | 22 ключа |
| **prometheus** (метрики) | ✅ Работает | локально :9090 |

---

## 🔗 API для Outline Manager

```
apiUrl: https://95.182.98.178:59163/kZibPEkVKanxRaN1JSs60w
certSha256: 90C39F1037C203EEFF20979689B03BD73632F7083C4248A3B68931062712EEA9
```

> ✅ IP в API URL совпадает с сервером — всё корректно.

---

## 🐳 Docker контейнеры

```
NAMES        STATUS             IMAGE
shadowbox    Up 2 hours         quay.io/outline/shadowbox:stable
watchtower   Up 2 hours         nickfedor/watchtower (автообновление)
```

### Службы (network mode: host)

| Порт | Назначение |
|------|-----------|
| `9091` | Shadowbox API (Node.js v18) |
| `9090` | Prometheus метрики |
| `9092` | outline-ss-server (Shadowsocks) |
| `59163` | Внешний API (с токеном) |
| `443` | HTTPS |
| `80` | HTTP |

### Shadowsocks порты и ключи (22 шт)

| Порт | Кол-во ключей |
|------|:------------:|
| `42361` | 4 |
| `33565` | 1 |
| `4770` | 1 |
| `49594` | 2 |
| `53194` | 10 |
| `17557` | 2 |
| `4906` | 2 |

---

## 🔧 iptables: MSS clamping (TCPMSS)

Shadowsocks шифрует каждый TCP-пакет, добавляя ~30+ байт оверхеда.  
Без MSS clamping большие пакеты не проходят — соединение устанавливается, но страницы не грузятся.

**Используется фиксированный MSS 1400 (OUTPUT + FORWARD):**

```bash
iptables -t mangle -A OUTPUT  -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1400
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1400
```

Проверить:
```bash
iptables -t mangle -vnL
```

> ✅ Правила сохранены в `/etc/iptables/rules.v4`, сервис `netfilter-persistent` включён.
> ⚠️ `set-mss 1400` вместо `clamp-to-pmtu`: в контексте Shadowsocks шифрованные пакеты не содержат SYN-флаги, поэтому clamp работает некорректно. Фиксированный MSS решает проблему PMTU blackhole.

---

## 📋 Команды управления

```bash
# Статус контейнеров
docker ps

# Логи shadowbox
docker logs shadowbox --tail 50

# Рестарт shadowbox
docker restart shadowbox

# Проверка API (список ключей)
curl -sk 'https://95.182.98.178:59163/kZibPEkVKanxRaN1JSs60w/access-keys'

# Проверка iptables MSS clamping
iptables -t mangle -vnL

# Обновить образы (watchtower сделает сам)
docker pull quay.io/outline/shadowbox:stable && docker restart shadowbox
```

---

## 💡 История

- Ранее в access.txt был указан неверный IP `194.120.24.137` (старый адрес).  
  После обновления shadowbox автоматически перегенерировал ключи с правильным IP `95.182.98.178`.  
  Резервная копия: `/opt/outline/access.txt.bak`
- **28.06.2026** — добавлен MSS clamping (TCPMSS) в iptables для устранения проблемы «подключается, но страницы не грузятся»
- **28.06.2026** — watchtower переустановлен, образ заменён на `nickfedor/watchtower`
- **28.06.2026** — замена `--clamp-mss-to-pmtu` на фиксированный MSS 1400:
  - `ERR_RELAY_CLIENT` на ключе 45 (порт 4906) — 25 ошибок из 72 попыток (37%)
  - `ERR_CIPHER` probes на портах: 4906 — 983, 4770 — 96 (сканирование, не проблема)
  - TCPMSS `clamp-to-pmtu` не всегда корректен с Shadowsocks, т.к. шифрованные пакеты не несут TCP SYN-флаги
  - Фиксированный MSS 1400 гарантирует прохождение пакетов через любые туннели
- **28.06.2026** — **IPv6 включён в ядре** (был отключён):
  - outline-ss-server биндит порты на `[::]` (IPv6 dual-stack)
  - При отключённом IPv6 в ядре `[::]` сокеты не принимали IPv4 соединения
  - Клиенты не могли подключиться: TCP connect успешен, но данные не доходили до обработчика
  - Включён: `sysctl net.ipv6.conf.all.disable_ipv6=0`
  - IPv6 на интерфейсах не настроен — публичного IPv6 адреса нет
  - MSS clamping сохранён в `/etc/iptables/rules.v4` (полный дамп `iptables-save`)

---

[← На главную](./index.md)