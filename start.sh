#!/bin/bash
# Production startup script for Proxmox Omni Healer
# This script activates the virtual environment and starts the FastAPI server

cd /opt/proxmox-omni-healer/backend
source /opt/proxmox-omni-healer/venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
