#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Missing .venv. Run ./install.sh first." >&2
  exit 1
fi

source .venv/bin/activate

exec uvicorn app:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
