#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR=$BASE_DIR/logs

mkdir -p "$LOG_DIR"

nohup "$BASE_DIR/infinite-loop.sh" \
  > "$LOG_DIR/infinite-loop-$(date +%F).out" \
  2>&1 &
  
echo "started infinite-loop.sh (pid=$!)"
