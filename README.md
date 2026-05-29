# Study-guide-generation

Generate curriculum-aligned study guides from structured teacher input.

## Workflow Automation

- Workspace-local GitHub Copilot workflow skills live under `.github/skills/`.
- The repo-level validation command for an implementation slice is `./scripts/validate-task.sh`.
- The live plain-language summary of shipped code lives in `CODEBASE_STATE.md` and should be refreshed by the `docs-drift` workflow.

## Validation Notes

- The backend currently pins `google-adk>=2.0.0b1,<2.1.0`, so parts of the upstream library surface are still beta or experimental.
- Backend pytest output intentionally filters two known Google ADK credential-service experimental `UserWarning`s so repeated upstream noise does not obscure real test failures.
- That filter is narrow: unrelated pytest warnings still surface and should be treated as actionable until reviewed.

## Workspace Layout

- `frontend/` contains the Next.js application.
- `backend/study-guide-agent/` is the canonical ADK backend project created with `agents-cli scaffold create`.

## Deployment

- The deployment source of truth is `DEPLOYMENT.md` at the repo root.
- The current recommended managed topology is Firebase App Hosting for the frontend and Cloud Run for the ADK backend.
- The frontend App Hosting configuration now lives in `frontend/apphosting.yaml` with the current staging override in `frontend/apphosting.staging.yaml`.
- The repo should support both a fast local dev loop and a production-like local parity mode so deployment bugs can be reproduced before and after remote releases.
- The repo-standardized local parity command is `./scripts/run-local-parity.sh`, which starts the production frontend against the local Cloud Run-style backend container.

The older root-level backend implementation has been retired in favor of the scaffolded project structure.
