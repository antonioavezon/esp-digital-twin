#!/bin/sh
set -eu

HOST="${ESP_CORE_HOST:-0.0.0.0}"
PORT="${ESP_CORE_PORT:-8080}"

exec uvicorn app.main:app --host "$HOST" --port "$PORT" --no-access-log
