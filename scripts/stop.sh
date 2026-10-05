#!/usr/bin/env bash
# Detiene y elimina los contenedores de la etapa 1C.
# No borra imágenes ni el código fuente.
set -euo pipefail
source "$(dirname "$0")/common.sh"

require_podman
ensure_env

podman compose --env-file .env down
echo "Servicios detenidos. Las imágenes locales se conservan."
