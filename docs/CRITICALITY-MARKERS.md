# Criticality Markers for AI Analysis

## Quick Reference

### 🔴 CRITICAL - Требует немедленного действия
- **Out of Memory (OOM)**: Контейнер может упасть
- **Disk Full**: Система не может писать данные
- **Critical Service Failures**: Основные приложения не работают

### 🟠 MEDIUM - Требует внимания
- **Connection Refused**: Сервисы не могут подключиться
- **Non-critical Service Failures**: Вспомогательные сервисы не работают

### 🟢 LOW - Информационно
- **systemd-networkd-wait-online timeout**: Известная проблема LXC
  - Не влияет на функциональность
  - Сеть работает нормально
  - Опционально отключить для ускорения apt операций

---

## Implementation in ai_agent.py

```python
# Criticality levels
criticality_map = {
    "oom": "CRITICAL",
    "disk_full": "CRITICAL",
    "systemd-networkd-wait-online": "LOW",
    "connection_refused": "MEDIUM",
    "service_failed": "MEDIUM"
}

# Overall criticality determination
max_criticality = "LOW"
if any(c == "CRITICAL" for c in criticality_map.values()):
    max_criticality = "CRITICAL"
elif any(c == "MEDIUM" for c in criticality_map.values()):
    max_criticality = "MEDIUM"
```

---

## UI Display Guidelines

### Color Coding
- 🔴 CRITICAL → Red background, urgent badge
- 🟠 MEDIUM → Yellow background, warning badge
- 🟢 LOW → Green background, info badge

### Action Buttons
- CRITICAL: "Fix Now" (prominent, red)
- MEDIUM: "Review & Fix" (yellow)
- LOW: "Optional Fix" (gray, collapsible)

---

## Known Issues & Resolutions

### Issue: systemd-networkd-wait-online timeout in LXC containers

**Status**: ✅ RESOLVED (Marked as LOW criticality)

**Root Cause**:
- systemd-networkd-wait-online waits for full network connectivity
- In LXC containers, this may never be fully satisfied
- This is a containerization limitation, not a configuration error

**Evidence**:
- Network interface is UP: `eth0@if17: <BROADCAST,MULTICAST,UP,LOWER_UP>`
- IP address is assigned: `inet 192.168.1.10/24 scope global eth0`
- Application is running normally
- Only affects apt operations (adds delay)

**Solution**:
```bash
systemctl disable systemd-networkd-wait-online.service
systemctl mask systemd-networkd-wait-online.service
```

**Why it's LOW criticality**:
- ✅ Network connectivity works
- ✅ Application functionality unaffected
- ✅ Only cosmetic issue in logs
- ✅ Optional to fix

---

**Last Updated**: 2026-04-23
**Version**: 1.0
