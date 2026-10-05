#!/bin/sh
set -eu

python - <<'PY'
import os
import sys
import time
import urllib.request

base = os.environ.get("ESP_CORE_BASE_URL", "http://esp-core:8080").rstrip("/")
url = base + "/api/v1/health"
last_error = "sin intento"

for _ in range(40):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status == 200:
                print("ESP-WEB | Connected to esp-core", flush=True)
                sys.exit(0)
            last_error = f"HTTP {response.status}"
    except Exception as exc:
        last_error = str(exc)
        time.sleep(1)

print(f"ESP-WEB | esp-core not reachable: {last_error}", flush=True)
sys.exit(1)
PY

PORT="${ESP_WEB_PORT:-8000}"
exec gunicorn espweb.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers 1 \
    --timeout 60 \
    --access-logfile /dev/null \
    --error-logfile -
