#!/bin/bash

# ==============================
# search-ad-keyword-monitor
# infinite loop runner
# (Google Chrome + headless)
# ==============================

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$BASE_DIR/venv/bin/python"
LOG_DIR="$BASE_DIR/logs"

mkdir -p "$LOG_DIR"

echo "[BOOT] $(date '+%Y-%m-%d %H:%M:%S') crawler shell started. shell_pid=$$" \
  >> "$LOG_DIR/monitor.log"

while true; do
  LOG_FILE="$LOG_DIR/monitor-$(date +%F).log"

  BATCH_START=$(date +%s)
  echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') start crawl" >> "$LOG_FILE"

  # ==============================
  # Chrome 잔재 정리 (Google Chrome 기준)
  # ==============================
  pkill -f google-chrome || true
  pkill -f chromedriver || true
  rm -rf /tmp/.com.google.Chrome.*
  rm -rf /tmp/ChromeProfile.*

  cd "$BASE_DIR" || exit 1

  # ==============================
  # Python 실행 (headless Chrome)
  # ==============================
  PYTHONPATH=. "$VENV_PYTHON" main.py >> "$LOG_FILE" 2>&1 &

  PY_PID=$!
  echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') python started. pid=$PY_PID" >> "$LOG_FILE"

  # Python 종료 대기
  wait "$PY_PID"
  EXIT_CODE=$?

  BATCH_END=$(date +%s)
  ELAPSED=$((BATCH_END - BATCH_START))

  echo "[WARN] $(date '+%Y-%m-%d %H:%M:%S') python exited. pid=$PY_PID exit_code=$EXIT_CODE elapsed=${ELAPSED}s" \
    >> "$LOG_FILE"

  # 다음 배치까지 대기
  sleep 15
done
