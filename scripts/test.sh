#!/usr/bin/env bash
# Ejecuta las pruebas dentro de las mismas imágenes que se despliegan.
set -euo pipefail
source "$(dirname "$0")/common.sh"

require_podman
ensure_env

echo "Construyendo imágenes de prueba..."
podman compose --env-file .env build

# Se usa podman run, no compose run: los servicios tienen container_name fijo
# y un segundo contenedor con el mismo nombre chocaría con el que deja start.sh.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo
echo "=== esp-core ==="
podman run --rm \
  -e ESP_DATA_ROOT=/app/data \
  -v "$ROOT/data:/app/data:ro,Z" \
  --entrypoint pytest \
  localhost/esp-digital-twin/esp-core:2-1 -q

echo
echo "=== esp-web ==="
podman run --rm --entrypoint python localhost/esp-digital-twin/esp-web:2-1 manage.py test anatomy
