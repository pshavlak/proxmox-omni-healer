# FastAPI сайт села Золотаревка
# Конфигурация

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SITE_TITLE = "Золотаревка"
SITE_DESC = "Неофициальный портал села"

# База данных
DATABASE_PATH = os.getenv("ZOLO_DATABASE_PATH", str(BASE_DIR / "zolotarevka.db"))

# Загрузка файлов
STATIC_DIR = str(BASE_DIR / "static")
ADMIN_DIR = str(BASE_DIR / "admin")
TEMPLATE_DIR = str(BASE_DIR / "templates")
UPLOAD_DIR = os.getenv("ZOLO_UPLOAD_DIR", str(BASE_DIR / "static" / "uploads"))
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".doc", ".docx", ".mp4"}

# Rate limiting для форм
SUGGEST_RATE_LIMIT = 5       # макс запросов
SUGGEST_RATE_WINDOW = 600    # за 10 минут

# Админ-панель (сессии через БД)
ADMIN_ENABLED = True
