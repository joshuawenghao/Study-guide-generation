#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend/study-guide-agent"
FRONTEND_DIR="$ROOT_DIR/frontend"

run_if_backend_tests_exist() {
  if find "$BACKEND_DIR/tests/unit" "$BACKEND_DIR/tests/integration" -type f \( -name 'test_*.py' -o -name '*_test.py' \) -print -quit 2>/dev/null | grep -q .; then
    echo "==> Running backend unit and integration tests"
    (
      cd "$BACKEND_DIR"
      uv run pytest tests/unit tests/integration
    )
  else
    echo "==> Skipping backend tests: no unit or integration tests found"
  fi
}

run_backend_lint() {
  if [[ -x "$BACKEND_DIR/agents-cli" ]]; then
    echo "==> Running backend lint"
    (
      cd "$BACKEND_DIR"
      ./agents-cli lint
    )
    echo "==> Running backend Pyright"
    (
      cd "$BACKEND_DIR"
      uv run pyright --project "$ROOT_DIR/pyrightconfig.json"
    )
  else
    echo "==> Skipping backend lint: agents-cli wrapper not found"
  fi
}

run_frontend_lint() {
  if [[ -f "$FRONTEND_DIR/package.json" ]] && grep -q '"lint"' "$FRONTEND_DIR/package.json"; then
    echo "==> Running frontend lint"
    (
      cd "$FRONTEND_DIR"
      npm run lint
    )
  else
    echo "==> Skipping frontend lint: no lint script found"
  fi
}

run_frontend_format_check() {
  if [[ -f "$FRONTEND_DIR/package.json" ]] && grep -q '"format:check"' "$FRONTEND_DIR/package.json"; then
    echo "==> Running frontend format check"
    (
      cd "$FRONTEND_DIR"
      npm run format:check
    )
  else
    echo "==> Skipping frontend format check: no format:check script found"
  fi
}

run_frontend_typecheck() {
  if [[ -f "$FRONTEND_DIR/package.json" ]] && grep -q '"typecheck"' "$FRONTEND_DIR/package.json"; then
    echo "==> Running frontend typecheck"
    (
      cd "$FRONTEND_DIR"
      npm run typecheck
    )
  else
    echo "==> Skipping frontend typecheck: no typecheck script found"
  fi
}

run_frontend_build() {
  if [[ -f "$FRONTEND_DIR/package.json" ]] && grep -q '"build"' "$FRONTEND_DIR/package.json"; then
    echo "==> Running frontend build"
    (
      cd "$FRONTEND_DIR"
      npm run build
    )
  else
    echo "==> Skipping frontend build: no build script found"
  fi
}

echo "==> Validating repository task slice"
run_backend_lint
run_if_backend_tests_exist
run_frontend_format_check
run_frontend_lint
run_frontend_typecheck
run_frontend_build
echo "==> Validation completed successfully"