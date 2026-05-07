# Workspace Skills

This directory contains workspace-local GitHub Copilot skills for the delivery workflow in this repository.

Current workflow entrypoints:

- `repo-automation` decides whether work should start from a new spec, an existing spec, or an existing task list.
- `spec-groom` turns a rough feature request into an implementation-ready spec delta.
- `spec-to-tasks` turns a spec into a task plan and a live status tracker.
- `task-implement` executes exactly one task slice with focused validation.
- `task-done` performs the done gate for a completed task slice, requires repo-wide validation, and creates a small commit.
- `docs-drift` reconciles documentation with the shipped code, including the live source-of-truth summary in `CODEBASE_STATE.md`.

These skills are designed for repository-local automation, not generic coding. They assume this repo's existing control documents remain authoritative:

- `IFC.md`
- `ARCHITECTURE.md`
- `TASKS.md`
- `TASK_STATUS.md`
- `.github/copilot-instructions.md`

The intended operating loop is:

1. Start with `repo-automation`.
2. Route to `spec-groom` and `spec-to-tasks` when a new or stale spec needs work.
3. Route to `task-implement` when an actionable task already exists.
4. Use `task-done` after implementation, focused validation, and `./scripts/validate-task.sh`.
5. Use `docs-drift` to sync documentation after code lands.
6. Repeat until `TASK_STATUS.md` shows no remaining implementation work.
