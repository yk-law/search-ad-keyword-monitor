#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[STOP] stopping search-ad-keyword-monitor..."

# 1. infinite-loop.sh (bash supervisor) 종료
pkill -f "$BASE_DIR/infinite-loop.sh" && \
  echo "[STOP] infinite-loop.sh stopped"

sleep 2

# 2. Python main.py 종료 ( --port 10002 제외 )
ps -ef \
  | grep "python.*main.py" \
  | grep -v -- "--port 10002" \
  | grep -v grep \
  | awk '{print $2}' \
  | xargs -r kill -9 && \
  echo "[STOP] python main.py stopped"

sleep 2

# 3. xvfb-run 종료
pkill -f "xvfb-run" && \
  echo "[STOP] xvfb stopped"

sleep 1

# 4. chromedriver 종료
pkill -f "chromedriver" && \
  echo "[STOP] chromedriver stopped"

sleep 1

# 5. chromium 종료 (최종 정리)
pkill -f "chromium-browser|/snap/chromium" && \
  echo "[STOP] chromium stopped"

sleep 1

echo "[STOP] done."

