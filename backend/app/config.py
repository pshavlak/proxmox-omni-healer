import os
from dotenv import load_dotenv
from pathlib import Path
from .logger import app_logger as logger

# Load config files in order (later files override earlier ones)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / "config.env")
load_dotenv(BASE_DIR / "config.env.local", override=True)

logger.info(f"Loading config from {BASE_DIR}")

class Config:
    # Proxmox API
    PROXMOX_HOST = os.getenv("PROXMOX_HOST", "192.168.1.100")
    PROXMOX_PORT = os.getenv("PROXMOX_PORT", "8006")
    PROXMOX_USER = os.getenv("PROXMOX_USER", "root@pam")
    PROXMOX_TOKEN_NAME = os.getenv("PROXMOX_TOKEN_NAME")
    PROXMOX_TOKEN_VALUE = os.getenv("PROXMOX_TOKEN_VALUE")
    PROXMOX_VERIFY_SSL = os.getenv("PROXMOX_VERIFY_SSL", "false").lower() == "true"
    
    # AI Agent
    CLAUDE_CODE_PATH = os.getenv("CLAUDE_CODE_PATH", "/usr/local/bin/claude")
    OMNIROUTE_PATH = os.getenv("OMNIROUTE_PATH", "/usr/local/bin/omniroute")
    AUTO_CONFIRM = os.getenv("AUTO_CONFIRM", "false").lower() == "true"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./db/omni_healer.db")
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8080"))

logger.info(f"Config loaded: Host={Config.PROXMOX_HOST}, Token configured={bool(Config.PROXMOX_TOKEN_VALUE)}")
