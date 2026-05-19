#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend/study-guide-agent"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_IMAGE="${BACKEND_IMAGE:-study-guide-agent-backend:local}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-study-guide-agent-parity}"
BACKEND_PORT="${BACKEND_PORT:-8080}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_ENV_FILE="${BACKEND_ENV_FILE:-$BACKEND_DIR/.env}"
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}"
FRONTEND_LOG="${FRONTEND_LOG:-/tmp/study-guide-parity-frontend.log}"
BACKEND_LOG="${BACKEND_LOG:-/tmp/study-guide-parity-backend.log}"
NEXT_TELEMETRY_DISABLED="${NEXT_TELEMETRY_DISABLED:-1}"

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 1
  fi
}

cleanup() {
  local exit_code="$?"

  if [[ -n "${frontend_pid:-}" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    kill "$frontend_pid" 2>/dev/null || true
    wait "$frontend_pid" 2>/dev/null || true
  fi

  if docker ps -a --format '{{.Names}}' | grep -Fxq "$BACKEND_CONTAINER"; then
    docker rm -f "$BACKEND_CONTAINER" >/dev/null 2>&1 || true
  fi

  exit "$exit_code"
}

ensure_docker_daemon() {
  if ! docker info >/dev/null 2>&1; then
    echo "Docker is installed but no daemon is available." >&2
    echo "Start Docker Desktop or Colima before running local parity." >&2
    exit 1
  fi
}

container_status() {
  local container_name="$1"
  docker inspect --format '{{.State.Status}}' "$container_name" 2>/dev/null || true
}

wait_for_url() {
  local url="$1"
  local label="$2"
  local log_file="$3"

  for _attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    if curl --silent --show-error --fail "$url" >/dev/null 2>&1; then
      return 0
    fi

    if [[ -n "${frontend_pid:-}" ]] && [[ "$label" == "frontend" ]] && ! kill -0 "$frontend_pid" 2>/dev/null; then
      echo "Frontend process exited before becoming ready." >&2
      [[ -f "$log_file" ]] && cat "$log_file" >&2
      return 1
    fi

    if [[ "$label" == "backend" ]]; then
      local status
      status="$(container_status "$BACKEND_CONTAINER")"

      if [[ "$status" == "exited" || "$status" == "dead" ]]; then
        echo "Backend container exited before becoming ready." >&2
        docker logs "$BACKEND_CONTAINER" >&2 || true
        return 1
      fi
    fi

    sleep 1
  done

  echo "Timed out waiting for $label at $url" >&2
  [[ -f "$log_file" ]] && cat "$log_file" >&2
  if [[ "$label" == "backend" ]]; then
    docker logs "$BACKEND_CONTAINER" >&2 || true
  fi
  return 1
}

require_command docker
require_command npm
require_command curl
ensure_docker_daemon

if [[ ! -f "$BACKEND_ENV_FILE" ]]; then
  echo "Backend env file not found: $BACKEND_ENV_FILE" >&2
  echo "Create backend/study-guide-agent/.env before running local parity." >&2
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run 'cd frontend && npm install' first." >&2
  exit 1
fi

trap cleanup EXIT INT TERM

echo "==> Building backend container image $BACKEND_IMAGE"
(
  cd "$BACKEND_DIR"
  docker build -t "$BACKEND_IMAGE" . >"$BACKEND_LOG" 2>&1
)

echo "==> Starting backend container $BACKEND_CONTAINER on port $BACKEND_PORT"
docker rm -f "$BACKEND_CONTAINER" >/dev/null 2>&1 || true
docker run \
  --name "$BACKEND_CONTAINER" \
  --rm \
  -p "$BACKEND_PORT:$BACKEND_PORT" \
  --env-file "$BACKEND_ENV_FILE" \
  -e PORT="$BACKEND_PORT" \
  -e BACKEND_CORS_ALLOW_ORIGINS="${BACKEND_CORS_ALLOW_ORIGINS:-http://127.0.0.1:$FRONTEND_PORT,http://localhost:$FRONTEND_PORT}" \
  "$BACKEND_IMAGE" >"$BACKEND_LOG" 2>&1 &

wait_for_url "$BACKEND_URL/docs" "backend" "$BACKEND_LOG"

echo "==> Building frontend in production mode"
(
  cd "$FRONTEND_DIR"
  ADK_BACKEND_URL="$BACKEND_URL" NEXT_TELEMETRY_DISABLED="$NEXT_TELEMETRY_DISABLED" npm run build
)

echo "==> Starting frontend on port $FRONTEND_PORT"
(
  cd "$FRONTEND_DIR"
  PORT="$FRONTEND_PORT" ADK_BACKEND_URL="$BACKEND_URL" NEXT_TELEMETRY_DISABLED="$NEXT_TELEMETRY_DISABLED" npm run start >"$FRONTEND_LOG" 2>&1
) &
frontend_pid=$!

wait_for_url "http://127.0.0.1:$FRONTEND_PORT/" "frontend" "$FRONTEND_LOG"

echo "==> Local parity stack is ready"
echo "Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "Backend:  $BACKEND_URL"
echo "Press Ctrl+C to stop both services"

wait "$frontend_pid"