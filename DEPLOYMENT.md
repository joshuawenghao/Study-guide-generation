# Deployment Guide

Last updated: 2026-05-12

This document is the deployment source of truth for the repository.
Use it together with `IFC.md`, `ARCHITECTURE.md`, `TASKS.md`, and `TASK_STATUS.md`.

## Goals

- Keep the production deployment aligned with the existing two-runtime architecture.
- Preserve the same browser -> Next.js -> ADK backend request flow across local and remote environments.
- Make production-only bugs reproducible locally through a production-like parity mode.
- Start deployment validation before final feature completion instead of waiting for a last-step release.

## Recommended deployment shape

The current recommended managed deployment is:

- **Frontend:** Vercel
- **Backend:** Google Cloud Run

This is the best default for the current repo because:

- the frontend is already a standard Next.js 14 app that benefits from Vercel preview environments and simple environment-variable management
- the backend is a Python ADK service with WeasyPrint and a Docker-based deployment path that maps naturally to Cloud Run
- the application is already designed as two runtimes connected by a single HTTP boundary, so there is no architectural rewrite required to deploy this way

## Alternatives considered

### Cloud Run for both frontend and backend

This would increase local-to-remote parity for the frontend runtime, but it adds operational work on the Next.js side without solving a current product constraint better than Vercel.

Use this alternative only if deployed Vercel behavior becomes the measured source of a production issue that cannot be reproduced or mitigated while keeping the thin proxy route.

### Direct browser-to-backend calls in production

This would remove the Next.js proxy from the production path, but it would make local and remote request flows diverge and would couple browser clients directly to backend origin changes.

Use this alternative only if deployed proxy behavior becomes a measured bottleneck for SSE or long-running request handling.

## Environment modes

| Mode           | Frontend runtime                  | Backend runtime                                          | Use when                                |
| -------------- | --------------------------------- | -------------------------------------------------------- | --------------------------------------- |
| Fast local dev | `npm run dev`                     | `uv run uvicorn app.fast_api_app:app --reload`           | Building features quickly               |
| Local parity   | production-mode Next.js runtime   | same container image intended for Cloud Run, run locally | Reproducing deployment-only bugs        |
| Remote dev     | Vercel preview or dev environment | separate dev Cloud Run service                           | Testing deployment after key milestones |
| Production     | Vercel production                 | Cloud Run production service                             | Serving users                           |

## Parity rules

Local parity mode should preserve these constraints:

- Keep separate frontend and backend runtimes.
- Keep the same frontend proxy behavior: browser -> Next.js -> backend.
- Route the frontend only through `ADK_BACKEND_URL`.
- Run the backend in the same container/runtime shape intended for Cloud Run.
- Inject configuration through environment variables and secrets rather than code edits.

Fast local dev is still the default development loop. Local parity exists for debugging deployment behavior, not for daily iteration speed.

## Environment and secret ownership

### Frontend

- `ADK_BACKEND_URL`
  - local dev: `http://localhost:8000`
  - local parity: local backend URL exposed by the parity stack
  - remote dev: dev Cloud Run service URL
  - production: production Cloud Run service URL

Store remote values in Vercel project environment settings. Do not hardcode backend URLs in the app.

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
- CORS allows the Vercel preview and production origins
- request timeout is set for long-running generation requests
- configuration comes from environment variables, not code edits

The repo currently includes a backend Dockerfile and `agents-cli deploy`, and the Dockerfile now installs the Linux runtime libraries WeasyPrint needs plus a build-time PDF smoke check. A local `docker build` now succeeds for that image definition in this workspace. However, the exact validated project-specific path still needs to be completed under Phase 13 because a real container run and Cloud Run-shaped parity check have not yet been verified here.

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
gcloud run deploy study-guide-agent-dev \
  --source backend/study-guide-agent \
  --region <region> \
  --set-env-vars MARKET_DEFAULT=PH \
  --set-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest
```

If the repo standardizes on a prebuilt image flow instead of `--source`, keep the same runtime contract: Cloud Run injects `PORT`, and the container must boot `app.fast_api_app:app` without code edits.

## Frontend deployment guidance

Deploy the frontend to Vercel with separate preview and production environments.

Frontend deployment requirements:

- the thin API proxy route remains the only path from the frontend to the backend
- preview environments point to the dev Cloud Run backend
- production points to the production Cloud Run backend
- environment switching is handled only through Vercel settings

## Staged deployment checkpoints

Do not postpone deployment testing until the full app is complete.
These checkpoints do **not** wait for all of Phase 13 to be complete. Phase 13 is partly cross-cutting: document and platform-setup tasks begin early, and the checkpoint tasks are executed when their prerequisite product phases are ready.

Run deployment checks at these milestones:

1. **After Phase 7:** deploy the backend to a dev environment and verify the real workflow can boot and accept a representative request.
2. **After Phase 10:** deploy the integrated frontend preview plus dev backend and verify the proxy and SSE path remotely.
3. **After Phase 12:** deploy a release candidate and run a smoke test covering submit, progress, preview, and PDF download.

Record the outcome of each checkpoint in `TASK_STATUS.md`.

## Current recommendation summary

- Keep **Vercel + Cloud Run** as the target deployment unless measured runtime limits prove otherwise.
- Add a **local parity** path rather than replacing the fast local dev loop.
- Validate deployment in **stages** after major milestones, not only at the end.
- Keep `DEPLOYMENT.md` as the detailed deployment reference and keep `ARCHITECTURE.md` aligned with any deployment changes.
