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

## Vercel deployment contract

The frontend deployment path assumes Vercel for hosting and Cloud Run for the backend.

Set `ADK_BACKEND_URL` in Vercel Project Settings instead of editing frontend code:

- `Development`: the local or shared dev backend URL when using Vercel's development environment
- `Preview`: the dev Cloud Run backend URL
- `Production`: the production Cloud Run backend URL

The proxy route at `frontend/app/api/generate/route.ts` must remain thin. It forwards requests to `ADK_BACKEND_URL` and does not contain environment-specific business logic. Switching preview and production backends should require only Vercel environment-variable changes.

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
