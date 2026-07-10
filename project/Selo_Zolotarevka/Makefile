# Makefile для сайта Золотаревка
# Автоматизация деплоя и обслуживания

.PHONY: help install run test backup deploy restart clean lint

help: ## Показать справку
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Установка зависимостей
	cd site && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

run: ## Запуск локального сервера (режим разработки)
	cd site && ZOLO_SECRET=local-dev .venv/bin/uvicorn app:app --reload --host 0.0.0.0 --port 8000

test: ## Быстрая проверка API
	@echo "=== Проверка сайта ==="
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@curl -s http://localhost:8000/api/pages | python3 -c "import sys,json; print(f'Страниц: {len(json.load(sys.stdin))}')"
	@curl -s http://localhost:8000/ | head -c 100
	@echo ""
	@echo "✅ Тест пройден"

# === Деплой ===

SERVER ?= root@zolotarevka.ru
REMOTE_DIR ?= /opt/zolotarevka
SERVICE ?= zolotarevka

deploy: ## Деплой на сервер: make deploy SERVER=user@host
	@echo "=== Деплой Золотаревка ==="
	ssh $(SERVER) "mkdir -p $(REMOTE_DIR)/backups $(REMOTE_DIR)/site"
	rsync -avz --delete \
		--exclude '.venv' \
		--exclude '.git' \
		--exclude '__pycache__' \
		--exclude '*.pyc' \
		--exclude '.DS_Store' \
		--exclude 'zolotarevka.db' \
		site/ $(SERVER):$(REMOTE_DIR)/site/
	rsync -avz deploy/ $(SERVER):$(REMOTE_DIR)/deploy/
	@echo "✅ Файлы скопированы"
	@echo "Запустите: make restart SERVER=$(SERVER)"

restart: ## Перезапуск сервиса на сервере
	ssh $(SERVER) "systemctl restart $(SERVICE) && systemctl status $(SERVICE) --no-pager | head -10"
	@echo "✅ Сервис перезапущен"

deploy-full: deploy restart ## Полный деплой (файлы + перезапуск)
	@echo "✅ Деплой завершён"

logs: ## Логи сервиса
	ssh $(SERVER) "journalctl -u $(SERVICE) -n 50 --no-pager"

# === Обслуживание ===

backup: ## Локальный бэкап
	./deploy/backup.sh

check-db: ## Проверка БД
	./deploy/check_db.sh

# === Очистка ===

clean: ## Очистка временных файлов
	find site -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find site -type f -name '*.pyc' -delete
	rm -rf site/.venv
	@echo "✅ Очищено"
