# Frontend

This directory contains the Next.js 14 frontend for the study-guide generation app.

## Local development

Install dependencies and start the dev server:

```bash
cd frontend
npm install
npm run dev
```

The frontend reads `ADK_BACKEND_URL` from `frontend/.env.local` during local development.

Local example:

```env
ADK_BACKEND_URL=http://localhost:8000
```

## Production and parity runs

Build and start the production frontend locally:

```bash
cd frontend
npm run build
ADK_BACKEND_URL=http://127.0.0.1:8080 npm run start
```

For the repo-standardized production-like local stack, use `./scripts/run-local-parity.sh` from the repository root.

## Firebase App Hosting deployment contract

The frontend deployment path assumes Firebase App Hosting for hosting and Cloud Run for the backend.

The checked-in App Hosting configuration files for this repo live at:

- `frontend/apphosting.yaml` for defaults that are safe across environments
- `frontend/apphosting.staging.yaml` for the current staging-only `ADK_BACKEND_URL` override

Set `ADK_BACKEND_URL` in Firebase App Hosting runtime configuration instead of editing frontend code:

- `Staging`: the staging Cloud Run backend URL
- `Production`: the production Cloud Run backend URL when a production environment is introduced

The proxy routes at `frontend/app/api/generate/route.ts` and `frontend/app/api/prompt-lab/generate/route.ts` must remain thin. They forward requests to `ADK_BACKEND_URL` and do not contain environment-specific business logic. Switching staging and later production backends should require only runtime environment-variable changes.

Use Firebase App Hosting rather than plain static Firebase Hosting. The current app depends on Next.js server-side route handlers for SSE proxying and prompt-lab transport, so a static export would break the shipped request flow.

For this monorepo, create the App Hosting backend against the repository root but set the app root directory to `frontend`. The current staging backend plan is:

- project: `manabie-ai`
- region: `asia-northeast1`
- backend name: `study-guide-frontend-staging`
- environment name: `staging`

After the backend is created, replace the placeholder value in `frontend/apphosting.staging.yaml` with the real staging Cloud Run URL and roll out again so the frontend proxy targets the deployed backend without code changes.

## Prompt-Lab reviewer page

The private reviewer flow now ships at `frontend/app/prompt-lab/page.tsx`.

- It loads curated backend samples through `frontend/app/api/prompt-lab/samples/route.ts` and `frontend/app/api/prompt-lab/samples/[sampleId]/route.ts`.
- It sends reviewer runs through `frontend/app/api/prompt-lab/generate/route.ts` to keep prompt-lab transport separate from the teacher flow.
- It reuses the existing `ProgressTracker`, `WebPreview`, and `DownloadButton` result surfaces for prompt-lab output review.

## Validation

The repo-level validation entrypoint is `./scripts/validate-task.sh` from the repository root. For frontend-only validation, the narrow checks are:

```bash
cd frontend
npm run format:check
npm run lint
npm run typecheck
npm run build
```

Focused prompt-lab frontend checks:

```bash
cd frontend
npm run test:prompt-lab
```
