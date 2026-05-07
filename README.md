# Study-guide-generation

Generate curriculum-aligned study guides from structured teacher input.

## Workflow Automation

- Workspace-local GitHub Copilot workflow skills live under `.github/skills/`.
- The repo-level validation command for an implementation slice is `./scripts/validate-task.sh`.
- The live plain-language summary of shipped code lives in `CODEBASE_STATE.md` and should be refreshed by the `docs-drift` workflow.

## Workspace Layout

- `frontend/` contains the Next.js application.
- `backend/study-guide-agent/` is the canonical ADK backend project created with `agents-cli scaffold create`.

The older root-level backend implementation has been retired in favor of the scaffolded project structure.
