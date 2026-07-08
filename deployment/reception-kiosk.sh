#!/usr/bin/env bash
set -euo pipefail

xset s off
xset -dpms
xset s noblank

chromium-browser \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 \
  http://localhost:5000/reception
