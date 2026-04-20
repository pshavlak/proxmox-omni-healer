"""
Configuration settings for Proxmox Omni-Healer
Copy this file to settings.py and update with your values
"""

# Proxmox VE Connection
PROXMOX_HOST = "192.168.1.100"  # Your Proxmox server IP
PROXMOX_PORT = 8006
PROXMOX_USER = "root@pam"  # or your API user
PROXMOX_PASSWORD = ""  # Not recommended, use token instead
PROXMOX_VERIFY_SSL = False  # Set to True in production with valid cert

# Proxmox API Token (recommended over password)
PROXMOX_TOKEN_NAME = ""  # e.g., "omni-healer"
PROXMOX_TOKEN_VALUE = ""  # The token value from Proxmox

# SSH Configuration for Guest Access
SSH_KEY_PATH = "/root/.ssh/id_ed25519"  # Path to private key
SSH_USERNAME = "root"  # Default username for guest access
SSH_TIMEOUT = 30

# AI Engine Configuration
CLAUDE_CODE_CLI_PATH = "/usr/local/bin/claude"  # Path to Claude Code CLI
OMNIROUTE_ENABLED = True
OMNIROUTE_CONFIG_PATH = "/etc/omniroute/config.yaml"

# Execution Modes
AUTO_HEAL_ENABLED = False  # Default: manual confirmation required
MAX_AUTO_COMMANDS_PER_HOUR = 10  # Limit for auto mode

# Database
DATABASE_URL = "sqlite+aiosqlite:///./data/omni_healer.db"

# Application Settings
APP_HOST = "0.0.0.0"
APP_PORT = 8000
DEBUG = False

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "/var/log/omni-healer/app.log"

# Security
SECRET_KEY = "change-this-to-a-random-secret-key"
TOKEN_EXPIRE_MINUTES = 60

# Monitoring Intervals (seconds)
SCAN_INTERVAL = 60  # How often to scan VMs/CTs
LOG_COLLECTION_INTERVAL = 30  # How often to collect logs
DOCKER_SCAN_INTERVAL = 120  # How often to check Docker containers
