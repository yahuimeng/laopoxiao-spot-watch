#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f config/settings.json ]; then
  cp config/settings.example.json config/settings.json
fi

if [ ! -f config/parking_slots.json ]; then
  cp config/parking_slots.example.json config/parking_slots.json
fi

echo "Bootstrap complete. Start with: source .venv/bin/activate && uvicorn app.main:app --reload"
