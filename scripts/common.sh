#!/usr/bin/env bash
# Funciones compartidas por los scripts de operación.
# Fedora Linux + Podman. No asume systemd ni podman-compose.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

require_podman() {
  if ! command -v podman >/dev/null 2>&1; then
    echo "No se encontró podman. En Fedora puede instalarse con: sudo dnf install podman" >&2
    exit 1
  fi
  if ! podman compose version >/dev/null 2>&1; then
    echo "podman compose no está disponible." >&2
    echo "Fedora 43 puede usar el proveedor docker-compose o el paquete podman-compose." >&2
    exit 1
  fi
  # En Fedora 43, `podman compose` delega en docker-compose, que habla con el
  # socket de la API de Podman. El servicio de usuario viene deshabilitado.
  local sock="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/podman/podman.sock"
  if [[ ! -S "$sock" ]]; then
    if ! systemctl --user start podman.socket; then
      echo "No se pudo iniciar podman.socket en ${sock}." >&2
      echo "Hace falta para que podman compose construya y levante los contenedores." >&2
      exit 1
    fi
  fi
  export DOCKER_HOST="unix://${sock}"
}

ensure_env() {
  if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Se creó .env a partir de .env.example"
  fi
}

load_env() {
  ensure_env
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
}

wait_http() {
  local url="$1"
  local attempt
  if ! command -v curl >/dev/null 2>&1; then
    echo "Se necesita curl para comprobar ${url}." >&2
    exit 1
  fi
  for attempt in $(seq 1 90); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "OK  ${url}"
      return 0
    fi
    sleep 1
  done
  echo "Tiempo agotado esperando ${url}" >&2
  echo "Revise los registros con: podman logs esp-core && podman logs esp-web" >&2
  return 1
}
