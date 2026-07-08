#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/VisionDesk"
LOG_FILE="${PROJECT_DIR}/visiondesk.log"

cd "${PROJECT_DIR}"

if ! curl -fsS http://localhost:5000/api/health >/dev/null 2>&1; then
  source "${PROJECT_DIR}/.venv/bin/activate"
  nohup python app.py >> "${LOG_FILE}" 2>&1 &
  sleep 4
fi

chromium-browser \
  --new-window \
  --noerrdialogs \
  --disable-infobars \
  http://localhost:5000/reception
