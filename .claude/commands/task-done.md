---
description: "Runs the done gate for a completed task slice: validates, checks ./scripts/validate-task.sh, updates TASK_STATUS.md, and optionally commits. Use after task-implement to confirm a task is truly complete or mark it partial. Triggers on: 'is the task done', 'mark task complete', 'run done gate', 'check if done', 'close out task'."
---

# Task Done

Use only after code for a single task slice exists. Runs the done gate, updates `TASK_STATUS.md`, and optionally creates a commit.

## Read First

- `TASKS.md`
- `TASK_STATUS.md`
- The files changed by `/task-implement`
- Relevant tests, lint commands, or typecheck commands for the touched slice

## Done Gate

A task can be marked `complete` only if **all** of the following are true:

1. The planned behavior exists in code.
2. At least one focused validation step passed.
3. `./scripts/validate-task.sh` passed without unresolved failures, including the backend Pyright pass.
4. The implementation does not violate repo instructions or architecture constraints.
5. Any required paired updates (e.g., mirrored type changes in both `types.py` and `types.ts`) are present.
6. `TASK_STATUS.md` notes match reality.
7. `CODEBASE_STATE.md` has been updated to reflect any changed shipped behavior, validation surfaces, or developer-facing capabilities (this update happens in the `/docs-drift` step that immediately follows — do not mark the task complete in git until that step is done).
8. If the task is deployment- or parity-related, the task-specific environment validation required by `TASKS.md` has passed, or any remaining blocked external step is recorded explicitly.

If any item fails, mark the task `partial` or keep it `not started` depending on actual state.

## Validation Workflow

1. Reuse the focused validation from `/task-implement`.
2. Require a successful `./scripts/validate-task.sh` run unless the user explicitly waives the done gate.
3. Treat backend Pyright failures as done-gate failures, even if `ty` and pytest pass.
4. For deployment or parity tasks, require the task-specific environment validation named in `TASKS.md`.
5. Record what was validated and what remains unverified.

## Repository-Specific Rules

- Update `TASK_STATUS.md` in the same turn when status changes.
- Do not edit `TASKS.md` unless the plan itself is now wrong.
- Only create a commit when the user has opted into iterative workflow commits.
- Stage only the files that belong to the completed task slice and related status/doc updates.
- Never include unrelated dirty files in the commit — if unrelated changes would be swept in, stop and ask the user how to proceed.
- Commit message format: `task(<task-id>): <imperative summary>` when the task ID is known (e.g. `task(4.1): implement wave 1 prompt templates`).
- If the work is a workflow or documentation slice without a task ID: `task: <imperative summary>`.

## Guardrails

- Do not mark work complete because it is mostly implemented.
- Do not hide missing tests or skipped validations.
- Do not use broad repo-wide test runs when a focused check is enough, unless the task truly crosses those boundaries.

## Expected Output

Return:

1. The final task status decision (`complete` / `partial` / `not started`).
2. The evidence supporting that decision.
3. The exact `TASK_STATUS.md` change made.
4. The commit created, or the blocker that prevented committing.
5. Whether the loop should continue to `/docs-drift` or back to `/task-implement`.
