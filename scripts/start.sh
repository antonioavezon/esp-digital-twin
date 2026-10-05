#!/usr/bin/env bash
# Construye y levanta ESP Digital Twin — Etapa 1C.
set -euo pipefail
source "$(dirname "$0")/common.sh"

require_podman
load_env

echo "Construyendo y arrancando contenedores (Fedora + Podman)..."
podman compose --env-file .env up -d --build

echo "Esperando healthchecks publicados en el host..."
wait_http "http://127.0.0.1:${ESP_CORE_HOST_PORT}/api/v1/health"
wait_http "http://127.0.0.1:${ESP_WEB_HOST_PORT}/health/"

echo
echo "ESP Digital Twin — Stage 1C"
echo "Web:      http://127.0.0.1:${ESP_WEB_HOST_PORT}/"
echo "Bomba:    http://127.0.0.1:${ESP_WEB_HOST_PORT}/pump/"
echo "Física:   http://127.0.0.1:${ESP_WEB_HOST_PORT}/physics/"
echo "Acerca:   http://127.0.0.1:${ESP_WEB_HOST_PORT}/about/"
echo "API:      http://127.0.0.1:${ESP_CORE_HOST_PORT}/api/v1/health"
