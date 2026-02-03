#!/bin/bash

BASE_DIR=/home/ccaca/search-ad-keyword-monitor
VENV_PYTHON=$BASE_DIR/venv/bin/python
LOG_DIR=$BASE_DIR/logs

mkdir -p "$LOG_DIR"

echo "[BOOT] $(date) crawler shell started. shell_pid=$$" >> "$LOG_DIR/monitor.log"

while true; do
  echo "[INFO] $(date) start crawl" >> "$LOG_DIR/monitor.log"

  # 크롬 잔재 정리
  pkill -f chromium || true
  rm -rf /tmp/.org.chromium.Chromium.scoped_dir.*

  cd "$BASE_DIR" || exit 1

  # Python 실행 (백그라운드로 띄워 PID 확보)
  PYTHONPATH=. xvfb-run -a -s "-screen 0 412x915x24" \
    "$VENV_PYTHON" main.py >> "$LOG_DIR/monitor.log" 2>&1 &

  PY_PID=$!
  echo "[INFO] $(date) python started. pid=$PY_PID" >> "$LOG_DIR/monitor.log"

  # Python 종료 대기
  wait $PY_PID
  EXIT_CODE=$?

  echo "[WARN] $(date) python exited. pid=$PY_PID exit_code=$EXIT_CODE" >> "$LOG_DIR/monitor.log"

  sleep 15
done
