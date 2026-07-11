# Деплой сайта Золотаревка

## 🏗️ Архитектура сети (Hybrid Cloud)

Сайт развернут по гибридной схеме для обеспечения безопасности и доступности:

1. **Входная точка (VPS)**: `31.56.208.248`
   - **Роль**: Только Reverse Proxy (Nginx).
   - **Функция**: Принимает HTTPS трафик с домена `золотаревка.рф` и перенаправляет его через туннель.
   - **Порт**: 80/443 $\to$ `127.0.0.1:8000` (через SSH-туннель).

2. **Транспорт (SSH Reverse Tunnel)**:
   - **Сервис**: `reverse-tunnel.service` (на базе `autossh`).
   - **Функция**: Пробрасывает порт 8000 с VPS на локальный сервер.
   - **Связь**: VPS (`10.0.0.1` / `31.56.208.248`) $\leftrightarrow$ LXC (`10.0.0.2` / `192.168.1.64`).

3. **Целевой сервер (LXC в Proxmox)**: `192.168.1.64`
   - **Роль**: Backend & Frontend (FastAPI).
   - **Путь к приложению**: `/var/www/zolotarevka-fastapi`
   - **Порт**: 8000.
   - **Окружение**: Python 3.x в виртуальном окружении `.venv`.

---

## 🚀 Быстрый старт (локально)

```bash
# Клонировать
git clone https://github.com/pshavlak/proxmox-omni-healer
cd proxmox-omni-healer/project/Selo_Zolotarevka

# Установить зависимости
make install

# Запустить (режим разработки)
export ZOLO_SECRET="my-secret-key"
make run
```

## 📦 Деплой на сервер

**ВАЖНО**: Деплой осуществляется напрямую на локальный сервер `192.168.1.64`.

```bash
# Полный деплой (файлы + перезапуск сервиса)
make deploy-full SERVER=root@192.168.1.64
```

### Особенности развертывания:
- **Путь на сервере**: `/var/www/zolotarevka-fastapi`.
- **Окружение**: Если после деплоя сайт выдает `Internal Server Error`, необходимо обновить зависимости:
  ```bash
  ssh root@192.168.1.64 "cd /var/www/zolotarevka-fastapi && bash install.sh"
  ```

## ⚙️ Системные сервисы

### 1. Приложение (FastAPI)
Сервис `zolotarevka.service` управляет запуском uvicorn.
- **Логи**: `journalctl -u zolotarevka -f`
- **Перезапуск**: `systemctl restart zolotarevka`

### 2. Туннель (Reverse SSH)
Сервис `reverse-tunnel.service` на VPS поддерживает связь с домашним сервером.
- **Команда восстановления**: `bash /tmp/fix-tunnel.sh` (на VPS).

## 🛠️ Makefile команды

| Команда | Описание |
|----------|-----------|
| `make help` | Справка по всем командам |
| `make install` | Создание .venv и установка зависимостей |
| `make run` | Локальный запуск сайта |
| `make deploy-full` | Синхронизация файлов с сервером и рестарт |
| `make logs` | Просмотр последних логов сервера |
| `make backup` | Создание бэкапа БД |
| `make check-db` | Проверка целостности базы данных |
