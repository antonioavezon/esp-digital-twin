#!/usr/bin/env bash
# Construye y levanta ESP Digital Twin — etapa 2-1.
set -euo pipefail
source "$(dirname "$0")/common.sh"

require_podman
load_env

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# El proceso del contenedor no es el usuario del host. Estas dos carpetas
# tienen que poder recibir la copia RAW y el inbox. No se tocan los xlsx de data/001.
mkdir -p "$ROOT/data/inbox" "$ROOT/data/datasets" "$ROOT/data/reports" "$ROOT/data/datasets/001/metadata" "$ROOT/data/datasets/001/derived"
chmod 0777 "$ROOT/data/inbox" "$ROOT/data/datasets"
# El contenedor tiene que poder reescribir el preprocess. No cambia el modo de los xlsx.
if [ -d "$ROOT/data/datasets/001/metadata" ]; then
  chmod 0777 "$ROOT/data/datasets/001/metadata" "$ROOT/data/datasets/001/derived"
fi

echo "Construyendo y arrancando contenedores (Fedora + Podman)..."
podman compose --env-file .env up -d --build

echo "Esperando healthchecks publicados en el host..."
wait_http "http://127.0.0.1:${ESP_CORE_HOST_PORT}/api/v1/health"
wait_http "http://127.0.0.1:${ESP_WEB_HOST_PORT}/health/"

echo
echo "ESP Digital Twin — Stage 2-1"
echo "Web:          http://127.0.0.1:${ESP_WEB_HOST_PORT}/"
echo "Bomba:        http://127.0.0.1:${ESP_WEB_HOST_PORT}/pump/"
echo "Física:       http://127.0.0.1:${ESP_WEB_HOST_PORT}/physics/"
echo "Investigación: http://127.0.0.1:${ESP_WEB_HOST_PORT}/research/"
echo "Acerca:       http://127.0.0.1:${ESP_WEB_HOST_PORT}/about/"
echo "API:          http://127.0.0.1:${ESP_CORE_HOST_PORT}/api/v1/health"
