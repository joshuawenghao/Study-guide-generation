# Deployment Guide

Last updated: 2026-05-28

This document is the deployment source of truth for the repository.
Use it together with `IFC.md`, `ARCHITECTURE.md`, `TASKS.md`, and `TASK_STATUS.md`.

## Goals

- Keep the production deployment aligned with the existing two-runtime architecture.
- Preserve the same browser -> Next.js -> ADK backend request flow across local and remote environments.
- Make production-only bugs reproducible locally through a production-like parity mode.
- Start deployment validation before final feature completion instead of waiting for a last-step release.

## Recommended deployment shape

The current recommended managed deployment is:

- **Frontend:** Firebase App Hosting
- **Backend:** Google Cloud Run

This is the best default for the current repo because:

- the frontend is already a standard Next.js 14 app with server routes and SSE proxying, which fits Firebase App Hosting without changing the browser -> Next.js -> backend flow
- the backend is a Python ADK service with WeasyPrint and a Docker-based deployment path that maps naturally to Cloud Run
- the application is already designed as two runtimes connected by a single HTTP boundary, so there is no architectural rewrite required to deploy this way

## Current rollout decisions

The current deployment plan is intentionally conservative:

- deploy manually first rather than introducing CI/CD before the remote path is proven
- stand up a single staging environment before defining a production release flow
- keep the existing two-runtime architecture unchanged: Firebase App Hosting frontend plus Cloud Run backend

The current staging decisions are:

- GCP project: `manabie-ai`
- Cloud Run region: `asia-northeast1`
- backend secret name: `GOOGLE_API_KEY`
- frontend App Hosting name: `study-guide-frontend-staging`
- backend Cloud Run service name: `study-guide-agent-staging`
- frontend runtime env var: `ADK_BACKEND_URL=<staging-cloud-run-url>`
- backend CORS pattern after the frontend exists: `http://localhost:3000,https://<firebase-app-hosting-staging-domain>`

Because both the Cloud Run service URL and the Firebase App Hosting staging domain are generated at provision time, the exact values are only known after the first manual staging deploy.

## Alternatives considered

### Cloud Run for both frontend and backend

This would increase local-to-remote parity for the frontend runtime, but it adds operational work on the Next.js side without solving a current product constraint better than Firebase App Hosting.

Use this alternative only if deployed App Hosting behavior becomes the measured source of a production issue that cannot be reproduced or mitigated while keeping the thin proxy route.

### Direct browser-to-backend calls in production

This would remove the Next.js proxy from the production path, but it would make local and remote request flows diverge and would couple browser clients directly to backend origin changes.

Use this alternative only if deployed proxy behavior becomes a measured bottleneck for SSE or long-running request handling.

## Environment modes

| Mode           | Frontend runtime                  | Backend runtime                                          | Use when                                |
| -------------- | --------------------------------- | -------------------------------------------------------- | --------------------------------------- |
| Fast local dev | `npm run dev`                     | `uv run uvicorn app.fast_api_app:app --reload`           | Building features quickly               |
| Local parity   | production-mode Next.js runtime   | same container image intended for Cloud Run, run locally | Reproducing deployment-only bugs        |
| Remote staging | Firebase App Hosting staging      | separate staging Cloud Run service                       | Testing deployment after key milestones |
| Production     | Firebase App Hosting production   | Cloud Run production service                             | Serving users                           |

## Parity rules

Local parity mode should preserve these constraints:

- Keep separate frontend and backend runtimes.
- Keep the same frontend proxy behavior: browser -> Next.js -> backend.
- Route the frontend only through `ADK_BACKEND_URL`.
- Run the backend in the same container/runtime shape intended for Cloud Run.
- Inject configuration through environment variables and secrets rather than code edits.

Fast local dev is still the default development loop. Local parity exists for debugging deployment behavior, not for daily iteration speed.

### Repo-standardized local parity command

The repo-standardized local parity entrypoint is:

```bash
./scripts/run-local-parity.sh
```

That command keeps the two-runtime split intact by:

- building the backend image from `backend/study-guide-agent/Dockerfile`
- running the backend container locally with the Cloud Run-style `PORT` contract
- loading backend secrets and config from `backend/study-guide-agent/.env`
- building the frontend in production mode and starting `next start`
- injecting `ADK_BACKEND_URL` so the frontend proxy talks to the local backend container without application code changes

Prerequisites:

- a running Docker daemon, for example Docker Desktop or Colima
- `backend/study-guide-agent/.env` present locally
- frontend dependencies installed with `cd frontend && npm install`

Default ports:

- frontend: `3000`
- backend: `8080`

You can override the defaults with environment variables such as `FRONTEND_PORT`, `BACKEND_PORT`, `BACKEND_IMAGE`, and `BACKEND_CONTAINER` when needed.

## Environment and secret ownership

### Frontend

- `ADK_BACKEND_URL`
  - local dev: `http://localhost:8000`
  - local parity: local backend URL exposed by the parity stack
  - remote staging: staging Cloud Run service URL
  - production: production Cloud Run service URL

Store remote values in Firebase App Hosting environment configuration. Do not hardcode backend URLs in the app.

### Backend

- `GOOGLE_API_KEY`
- `MARKET_DEFAULT`
- any future CORS allowlist variables or deployment-specific runtime settings

Store remote secrets in Google Cloud-managed secret or environment configuration. Do not expose backend secrets to the frontend.

## Backend deployment guidance

The backend should be deployed to Cloud Run from the same container image definition used for local parity.

Backend deployment requirements:

- container boots the FastAPI app
- runtime port is configurable
- WeasyPrint system dependencies are present in the image
- CORS allows the Firebase App Hosting staging and production origins
- request timeout is set for long-running generation requests
- configuration comes from environment variables, not code edits

The repo currently includes a backend Dockerfile and `agents-cli deploy`, and the Dockerfile now installs the Linux runtime libraries WeasyPrint needs plus a build-time PDF smoke check. The project-specific local parity path is now standardized and validated through `./scripts/run-local-parity.sh`, which runs the same backend image shape locally while serving the frontend through its production Next.js runtime.

### Backend container commands

Use the same image definition for both local parity and Cloud Run.

Local build:

```bash
cd backend/study-guide-agent
docker build -t study-guide-agent-backend:local .
```

Local run with the Cloud Run-style runtime contract:

```bash
docker run --rm \
  -p 8080:8080 \
  -e PORT=8080 \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  -e MARKET_DEFAULT=PH \
  study-guide-agent-backend:local
```

The container entrypoint reads `PORT` from the environment, so the same image can also be run on a different local port when needed:

```bash
docker run --rm \
  -p 8090:8090 \
  -e PORT=8090 \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  -e MARKET_DEFAULT=PH \
  study-guide-agent-backend:local
```

Cloud Run deploy shape:

```bash
gcloud run deploy study-guide-agent-staging \
  --source backend/study-guide-agent \
  --region <region> \
  --set-env-vars MARKET_DEFAULT=PH \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest
```

If the repo standardizes on a prebuilt image flow instead of `--source`, keep the same runtime contract: Cloud Run injects `PORT`, and the container must boot `app.fast_api_app:app` without code edits.

### Standard backend deploy entrypoint

The repo-standardized backend deploy command is:

```bash
./scripts/deploy-backend-cloud-run.sh <dev|prod>
```

Required environment variables for that command:

- `GCP_PROJECT_ID`
- `CLOUD_RUN_REGION`
- `BACKEND_CORS_ALLOW_ORIGINS`

Optional environment variables supported by the script:

- `CLOUD_RUN_SERVICE`
- `GOOGLE_API_KEY_SECRET_NAME`
- `MARKET_DEFAULT`
- `CLOUD_RUN_TIMEOUT`
- `CLOUD_RUN_CONCURRENCY`
- `CLOUD_RUN_MEMORY`
- `CLOUD_RUN_CPU`
- `TRACE_TO_CLOUD`
- `OTEL_TO_CLOUD`
- `SESSION_SERVICE_URI`
- `ARTIFACT_SERVICE_URI`

The backend runtime now reads these deployment-facing environment variables directly:

- `BACKEND_CORS_ALLOW_ORIGINS` as a comma-separated list for FastAPI CORS allow-origins
- `SESSION_SERVICE_URI` and `ARTIFACT_SERVICE_URI` for optional remote service wiring
- `TRACE_TO_CLOUD` and `OTEL_TO_CLOUD` for telemetry export toggles
- `PORT` for the Cloud Run runtime port injected at startup

### Cloud Run service assumptions

The current repo default assumptions for long-running generation requests are:

- timeout: `900` seconds
- concurrency: `1` request per instance
- unauthenticated access: enabled for the prototype backend, with browser traffic still expected to arrive through the frontend proxy

These values are intentionally conservative because study-guide generation can involve multiple model calls plus PDF rendering in one request.

### CORS origin guidance

For the staging Cloud Run service, `BACKEND_CORS_ALLOW_ORIGINS` should include only the origins that need to call the backend directly in that environment, typically:

- local frontend development origin, e.g. `http://localhost:3000`
- the active Firebase App Hosting staging frontend origin once Phase 13.5 is in place

For the production Cloud Run service, `BACKEND_CORS_ALLOW_ORIGINS` should include only the production frontend origin or custom domains.

Example staging deployment using the current script:

```bash
GCP_PROJECT_ID=<project-id> \
CLOUD_RUN_REGION=<region> \
CLOUD_RUN_SERVICE=study-guide-agent-staging \
BACKEND_CORS_ALLOW_ORIGINS=http://localhost:3000,https://<firebase-app-hosting-staging-domain> \
./scripts/deploy-backend-cloud-run.sh dev
```

Example production deployment:

```bash
GCP_PROJECT_ID=<project-id> \
CLOUD_RUN_REGION=<region> \
BACKEND_CORS_ALLOW_ORIGINS=https://<production-domain> \
./scripts/deploy-backend-cloud-run.sh prod
```

## Frontend deployment guidance

Deploy the frontend to Firebase App Hosting, starting with a single staging environment.

Frontend deployment requirements:

- the thin API proxy route remains the only path from the frontend to the backend
- the staging environment points to the staging Cloud Run backend
- production, when introduced, points to the production Cloud Run backend
- environment switching is handled only through App Hosting runtime configuration

### Firebase App Hosting environment settings

Set `ADK_BACKEND_URL` in Firebase App Hosting runtime configuration instead of committing deployed values to the repo:

- `Staging`: the staging Cloud Run service URL
- `Production`: the production Cloud Run service URL when that environment exists

This keeps the frontend deployment path environment-driven. The same built app and the same proxy route can be used across staging and later production; only the App Hosting environment value changes.

The repo now checks in Firebase App Hosting config files under the frontend app root:

- `frontend/apphosting.yaml` for shared App Hosting runtime defaults
- `frontend/apphosting.staging.yaml` for the current staging-only runtime `ADK_BACKEND_URL` override

The proxy route at `frontend/app/api/generate/route.ts` is already compatible with this contract because it reads `ADK_BACKEND_URL` at runtime and forwards requests without embedding backend-specific business logic.

The prompt-lab proxy route at `frontend/app/api/prompt-lab/generate/route.ts` uses the same backend base URL contract, so one `ADK_BACKEND_URL` value is sufficient for both the teacher flow and the reviewer-only prompt-lab flow.

### Frontend deployment checklist

Before considering the frontend Firebase App Hosting path configured, confirm all of the following:

- `ADK_BACKEND_URL` is set in App Hosting Staging to the staging Cloud Run backend URL
- if production is introduced later, `ADK_BACKEND_URL` is set there to the production Cloud Run backend URL
- no frontend code or committed env file changes are required when switching environments
- the backend `BACKEND_CORS_ALLOW_ORIGINS` value includes `http://localhost:3000` plus the active staging App Hosting domain during staging
- when production is introduced later, the production backend allowlist includes only the production frontend origin or custom domain

### Frontend hosting compatibility note

The current frontend is not compatible with plain static Firebase Hosting because it relies on Next.js server-side route handlers for SSE proxying and prompt-lab transport. Use Firebase App Hosting or another server-capable Next.js hosting target; do not flatten the frontend into a static export for the current app shape.

### Manual staging flow

The minimal staging sequence is:

1. Deploy the backend Cloud Run service first and record the generated service URL.
2. Create the Firebase App Hosting staging frontend in `manabie-ai` with backend name `study-guide-frontend-staging`, region `asia-northeast1`, environment name `staging`, and app root directory `frontend`.
3. Set `ADK_BACKEND_URL` to the backend URL by replacing the placeholder value in `frontend/apphosting.staging.yaml` or by setting the same variable in the Firebase console.
3. Record the generated App Hosting staging domain.
4. Update `BACKEND_CORS_ALLOW_ORIGINS` on the backend to `http://localhost:3000,https://<firebase-app-hosting-staging-domain>`.
5. Re-run the backend deploy so the staging frontend origin is allowed remotely.

If the staging frontend does not exist yet, it is acceptable to bootstrap the backend first with `BACKEND_CORS_ALLOW_ORIGINS=http://localhost:3000` and then expand the allowlist after the App Hosting domain is known.

## Staged deployment checkpoints

Do not postpone deployment testing until the full app is complete.
These checkpoints do **not** wait for all of Phase 13 to be complete. Phase 13 is partly cross-cutting: document and platform-setup tasks begin early, and the checkpoint tasks are executed when their prerequisite product phases are ready.

Run deployment checks at these milestones:

1. **After Phase 7:** deploy the backend to the current non-production environment and verify the real workflow can boot and accept a representative request.
2. **After Phase 10:** deploy the integrated staging frontend plus staging backend and verify the proxy and SSE path remotely.
3. **After Phase 12:** deploy a release candidate and run a smoke test covering submit, progress, preview, and PDF download.

Record the outcome of each checkpoint in `TASK_STATUS.md`.

## Current recommendation summary

- Keep **Firebase App Hosting + Cloud Run** as the target deployment unless measured runtime limits prove otherwise.
- Add a **local parity** path rather than replacing the fast local dev loop.
- Validate deployment in **stages** after major milestones, not only at the end.
- Keep `DEPLOYMENT.md` as the detailed deployment reference and keep `ARCHITECTURE.md` aligned with any deployment changes.
