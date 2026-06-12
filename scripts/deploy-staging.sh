#!/usr/bin/env bash
# deploy-staging.sh — one-command staging deploy for backend and/or frontend.
#
# Usage:
#   ./scripts/deploy-staging.sh              # deploy backend then frontend
#   ./scripts/deploy-staging.sh --backend    # backend only
#   ./scripts/deploy-staging.sh --frontend   # frontend only
#   ./scripts/deploy-staging.sh --dry-run    # print commands without running
#
# The script reads GOOGLE_API_KEY and MARKET_DEFAULT from
# backend/study-guide-agent/.env automatically — no env exports needed.
# It uses the literal GOOGLE_API_KEY env-var workaround (not Secret Manager)
# because the staging service account does not yet have Secret Manager access.

set -euo pipefail

# ---------------------------------------------------------------------------
# Staging constants — update these if the staging environment changes
# ---------------------------------------------------------------------------
GCP_PROJECT="manabie-ai"
CLOUD_RUN_REGION="asia-northeast1"
BACKEND_SERVICE="study-guide-agent-staging"
FIREBASE_BACKEND="study-guide-frontend-staging"
CORS_ORIGINS="http://localhost:3000,https://study-guide-frontend-staging--manabie-ai.asia-southeast1.hosted.app"
GEMINI_MODEL="gemini-3.5-flash"
MEMORY="2Gi"
CPU="1"
CONCURRENCY="1"
TIMEOUT="900"
# ---------------------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/backend/study-guide-agent/.env"

# Parse arguments
deploy_backend=true
deploy_frontend=true
dry_run=false

for arg in "$@"; do
  case "$arg" in
    --backend)   deploy_frontend=false ;;
    --frontend)  deploy_backend=false ;;
    --dry-run)   dry_run=true ;;
    -h|--help)
      sed -n '2,10p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: $0 [--backend|--frontend] [--dry-run]" >&2
      exit 1
      ;;
  esac
done

# Load .env — need GOOGLE_API_KEY and MARKET_DEFAULT
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: $ENV_FILE not found. Create it from .env.example first." >&2
  exit 1
fi

# shellcheck source=/dev/null
set -o allexport
source "$ENV_FILE"
set +o allexport

: "${GOOGLE_API_KEY:?GOOGLE_API_KEY must be set in backend/study-guide-agent/.env}"
MARKET="${MARKET_DEFAULT:-PH}"

run() {
  echo ""
  echo "▶ $*"
  if [[ "$dry_run" == false ]]; then
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# Backend — Cloud Run via source deploy with literal API key env var
# ---------------------------------------------------------------------------
if [[ "$deploy_backend" == true ]]; then
  echo "==> Deploying backend to Cloud Run ($BACKEND_SERVICE)"
  run gcloud run deploy "$BACKEND_SERVICE" \
    --project "$GCP_PROJECT" \
    --region "$CLOUD_RUN_REGION" \
    --source "$ROOT_DIR/backend/study-guide-agent" \
    --memory "$MEMORY" \
    --cpu "$CPU" \
    --concurrency "$CONCURRENCY" \
    --timeout "$TIMEOUT" \
    --set-env-vars "^@^MARKET_DEFAULT=${MARKET}@BACKEND_CORS_ALLOW_ORIGINS=${CORS_ORIGINS}@TRACE_TO_CLOUD=false@OTEL_TO_CLOUD=false@GEMINI_MODEL=${GEMINI_MODEL}@GOOGLE_API_KEY=${GOOGLE_API_KEY}" \
    --allow-unauthenticated
  echo ""
  echo "Backend deployed"
fi

# ---------------------------------------------------------------------------
# Frontend — Firebase App Hosting local-source deploy
# ---------------------------------------------------------------------------
if [[ "$deploy_frontend" == true ]]; then
  echo "==> Deploying frontend to Firebase App Hosting ($FIREBASE_BACKEND)"
  run npx firebase-tools deploy \
    --only "apphosting:$FIREBASE_BACKEND" \
    --project "$GCP_PROJECT"
  echo ""
  echo "Frontend deployed"
fi

if [[ "$dry_run" == true ]]; then
  echo ""
  echo "(dry-run — no changes made)"
fi
