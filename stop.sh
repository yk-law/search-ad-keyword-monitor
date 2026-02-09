#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[STOP] stopping search-ad-keyword-monitor..."

# 1. infinite-loop.sh 먼저 강제 종료 (재기동 방지)
pkill -9 -f "$BASE_DIR/infinite-loop.sh" && \
  echo "[STOP] infinite-loop.sh killed"

sleep 1

# 2. 크롤러용 main.py만 종료 (알림 서버 제외)
# 조건:
#  - BASE_DIR 경로 포함
#  - '--port 10002' 없는 프로세스만
ps -ef \
  | grep "$BASE_DIR/main.py" \
  | grep -v grep \
  | grep -v "--port 10002" \
  | awk '{print $2}' \
  | xargs -r kill -9 && \
  echo "[STOP] crawler main.py killed"

sleep 1

# 3. chromium 계열 강제 정리 (남아 있으면만)
pkill -9 -f "/snap/bin/chromium" || true
pkill -9 -f "chromium" || true

sleep 1

echo "[STOP] done."
