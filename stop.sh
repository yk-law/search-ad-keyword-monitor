#!/bin/bash

BASE_DIR=/home/ccaca/search-ad-keyword-monitor

echo "[STOP] stopping search-ad-keyword-monitor..."

# 1. infinite-loop.sh (bash supervisor) 종료
pkill -f "$BASE_DIR/infinite-loop.sh" && \
  echo "[STOP] infinite-loop.sh stopped"

sleep 2

# 2. Python main.py 종료
pkill -f "$BASE_DIR/main.py" && \
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

# 6. zombie cleanup (부모 죽었는데 남은 경우 대비)
sleep 1

echo "[STOP] done."

