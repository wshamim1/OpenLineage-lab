#!/usr/bin/env bash

# Compose wrapper for OpenLineage-lab.
# Auto-detects Docker or Podman and runs compose with install-scripts/docker-compose.yml.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
  cat <<'EOF'
Usage:
  ./compose.sh <compose-subcommand> [options]

Examples:
  ./compose.sh up -d
  ./compose.sh down
  ./compose.sh ps
  ./compose.sh logs -f marquez-api

Optional environment variable:
  CONTAINER_RUNTIME=docker|podman
    Force runtime selection instead of auto-detection.
EOF
}

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo -e "${RED}Error: compose file not found at ${COMPOSE_FILE}${NC}"
  exit 1
fi

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" || "$#" -eq 0 ]]; then
  usage
  exit 0
fi

RUNTIME="${CONTAINER_RUNTIME:-auto}"
COMPOSE_CMD=()

docker_daemon_ready() {
  docker info >/dev/null 2>&1
}

select_docker() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 && docker_daemon_ready; then
    COMPOSE_CMD=(docker compose)
    return 0
  fi

  if command -v docker-compose >/dev/null 2>&1 && docker_daemon_ready; then
    COMPOSE_CMD=(docker-compose)
    return 0
  fi

  return 1
}

select_podman() {
  if ! command -v podman >/dev/null 2>&1; then
    return 1
  fi

  if [[ "${OSTYPE:-}" == darwin* ]]; then
    if podman machine list 2>/dev/null | grep -q "Currently running"; then
      :
    else
      echo -e "${YELLOW}Podman machine is not running. Attempting to start...${NC}"
      if ! podman machine list 2>/dev/null | grep -q "podman-machine-default"; then
        podman machine init >/dev/null
      fi
      podman machine start >/dev/null
    fi
  fi

  if podman compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(podman compose)
    return 0
  fi

  if command -v podman-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(podman-compose)
    return 0
  fi

  return 1
}

case "${RUNTIME}" in
  docker)
    if ! select_docker; then
      echo -e "${RED}Error: Docker compose is unavailable or Docker daemon is not running.${NC}"
      echo "Start Docker Desktop (or your Docker daemon), then retry."
      exit 1
    fi
    ;;
  podman)
    if ! select_podman; then
      echo -e "${RED}Error: Podman compose is not available.${NC}"
      exit 1
    fi
    ;;
  auto)
    if select_docker; then
      :
    elif select_podman; then
      :
    else
      echo -e "${RED}Error: No supported compose runtime found.${NC}"
      echo "Install one of:"
      echo "  - Docker with 'docker compose' (or docker-compose)"
      echo "  - Podman with 'podman compose' (or podman-compose)"
      exit 1
    fi
    ;;
  *)
    echo -e "${RED}Error: Invalid CONTAINER_RUNTIME='${RUNTIME}'. Use docker, podman, or auto.${NC}"
    exit 1
    ;;
esac

echo -e "${GREEN}Using runtime: ${COMPOSE_CMD[*]}${NC}"
echo -e "${GREEN}Compose file: ${COMPOSE_FILE}${NC}"

"${COMPOSE_CMD[@]}" -f "${COMPOSE_FILE}" "$@"
