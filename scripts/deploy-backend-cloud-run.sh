#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/deploy-backend-cloud-run.sh <dev|prod> [--dry-run]

Required environment variables:
  GCP_PROJECT_ID                Google Cloud project id
  CLOUD_RUN_REGION              Cloud Run region, e.g. us-central1
  BACKEND_CORS_ALLOW_ORIGINS    Comma-separated allowed frontend origins

Optional environment variables:
  CLOUD_RUN_SERVICE             Override default service name (study-guide-agent-<env>)
  GOOGLE_API_KEY_SECRET_NAME    Secret Manager secret for GOOGLE_API_KEY (default: GOOGLE_API_KEY)
  MARKET_DEFAULT                Default market (default: PH)
  CLOUD_RUN_TIMEOUT             Request timeout in seconds (default: 900)
  CLOUD_RUN_CONCURRENCY         Max concurrent requests per instance (default: 1)
  CLOUD_RUN_MEMORY              Memory allocation, e.g. 2Gi (default: 2Gi)
  CLOUD_RUN_CPU                 CPU allocation, e.g. 1 or 2 (default: 1)
  TRACE_TO_CLOUD                Enable Cloud Trace export (default: false)
  OTEL_TO_CLOUD                 Enable OpenTelemetry cloud export (default: false)
  SESSION_SERVICE_URI           Optional remote session service URI
  ARTIFACT_SERVICE_URI          Optional remote artifact service URI

Example:
  GCP_PROJECT_ID=my-project \
  CLOUD_RUN_REGION=us-central1 \
  BACKEND_CORS_ALLOW_ORIGINS=https://my-staging-app.web.app,http://localhost:3000 \
  ./scripts/deploy-backend-cloud-run.sh dev --dry-run
EOF
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" || ${1:-} == "" ]]; then
  usage
  exit 0
fi

environment="$1"
shift

dry_run=false
if [[ ${1:-} == "--dry-run" ]]; then
  dry_run=true
  shift
fi

if [[ $# -gt 0 ]]; then
  usage
  exit 1
fi

if [[ "$environment" != "dev" && "$environment" != "prod" ]]; then
  echo "Environment must be 'dev' or 'prod'." >&2
  exit 1
fi

: "${GCP_PROJECT_ID:?GCP_PROJECT_ID is required}"
: "${CLOUD_RUN_REGION:?CLOUD_RUN_REGION is required}"
: "${BACKEND_CORS_ALLOW_ORIGINS:?BACKEND_CORS_ALLOW_ORIGINS is required}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend/study-guide-agent"

service_name="${CLOUD_RUN_SERVICE:-study-guide-agent-$environment}"
google_api_key_secret_name="${GOOGLE_API_KEY_SECRET_NAME:-GOOGLE_API_KEY}"
market_default="${MARKET_DEFAULT:-PH}"
cloud_run_timeout="${CLOUD_RUN_TIMEOUT:-900}"
cloud_run_concurrency="${CLOUD_RUN_CONCURRENCY:-1}"
cloud_run_memory="${CLOUD_RUN_MEMORY:-2Gi}"
cloud_run_cpu="${CLOUD_RUN_CPU:-1}"
trace_to_cloud="${TRACE_TO_CLOUD:-false}"
otel_to_cloud="${OTEL_TO_CLOUD:-false}"

env_vars="^@^MARKET_DEFAULT=${market_default}@BACKEND_CORS_ALLOW_ORIGINS=${BACKEND_CORS_ALLOW_ORIGINS}@TRACE_TO_CLOUD=${trace_to_cloud}@OTEL_TO_CLOUD=${otel_to_cloud}"

if [[ -n ${SESSION_SERVICE_URI:-} ]]; then
  env_vars="${env_vars}@SESSION_SERVICE_URI=${SESSION_SERVICE_URI}"
fi

if [[ -n ${ARTIFACT_SERVICE_URI:-} ]]; then
  env_vars="${env_vars}@ARTIFACT_SERVICE_URI=${ARTIFACT_SERVICE_URI}"
fi

cmd=(
  gcloud run deploy "$service_name"
  --project "$GCP_PROJECT_ID"
  --region "$CLOUD_RUN_REGION"
  --source "$BACKEND_DIR"
  --memory "$cloud_run_memory"
  --cpu "$cloud_run_cpu"
  --concurrency "$cloud_run_concurrency"
  --timeout "$cloud_run_timeout"
  --set-env-vars "$env_vars"
  --set-secrets "GOOGLE_API_KEY=${google_api_key_secret_name}:latest"
  --allow-unauthenticated
)

printf 'Deploy command:\n'
printf ' %q' "${cmd[@]}"
printf '\n'

if [[ "$dry_run" == true ]]; then
  exit 0
fi

"${cmd[@]}"