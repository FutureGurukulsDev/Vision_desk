#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/VisionDesk"

cd "${PROJECT_DIR}"
source "${PROJECT_DIR}/.venv/bin/activate"
python app.py
