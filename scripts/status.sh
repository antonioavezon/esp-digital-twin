#!/usr/bin/env bash
# Muestra el estado de los contenedores y su healthcheck.
set -euo pipefail
source "$(dirname "$0")/common.sh"

require_podman
ensure_env

podman compose --env-file .env ps
echo
podman ps -a --filter name=esp-core --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
podman ps -a --filter name=esp-web --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo
if podman inspect esp-core esp-web >/dev/null 2>&1; then
  podman inspect --format '{{.Name}} status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}' esp-core esp-web
else
  echo "Los contenedores esp-core y esp-web no están creados. Ejecute ./scripts/start.sh"
fi
