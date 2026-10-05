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
echo
echo "=== esp-core ==="
podman run --rm --entrypoint pytest localhost/esp-digital-twin/esp-core:1c -q

echo
echo "=== esp-web ==="
podman run --rm --entrypoint python localhost/esp-digital-twin/esp-web:1c manage.py test anatomy
