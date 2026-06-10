---
description: "Implements exactly one task from TASKS.md with focused validation. Use when tasks already exist and the goal is to write code for a specific task slice. Triggers on: 'implement task', 'code task', 'work on task', 'implement [task id]', 'start coding'."
---

# Task Implement

Use for the coding slice of the delivery loop. Takes one concrete task from plan to implemented-with-focused-validation, keeping scope narrow and reversible.

Optionally pass a task ID as an argument: `/task-implement 4.1`

## Read First

- `TASKS.md`
- `TASK_STATUS.md`
- `DEPLOYMENT.md` when implementing deployment, parity, or remote-validation tasks
- `CLAUDE.md`
- The nearest owning implementation files for the chosen task

## Task Selection Rules

- Prefer the next `not started` task, or the one matching `$ARGUMENTS` if provided.
- If the next relevant item is `partial`, resume the smallest unfinished slice.
- Do not pick multiple tasks in one pass unless the task definition itself must be split.

## Execution Contract

1. State the exact task being implemented.
2. Use **TodoWrite** to break the task into sub-steps before writing code.
3. Identify the nearest code path that controls the behavior.
4. Form one falsifiable local hypothesis.
5. Make the smallest grounded edit that tests that hypothesis.
6. Run the narrowest focused validation available immediately after the first substantive edit.
7. Repair locally if validation exposes a defect.
8. Stop when the slice is implemented and validated enough for `/task-done` to evaluate.

## Repository-Specific Rules

- Keep backend work inside `backend/study-guide-agent/`.
- Keep frontend work inside `frontend/`.
- When contract types change, update both `backend/study-guide-agent/app/types.py` and `frontend/lib/types.ts` in the same implementation pass.
- Do not mark the task complete here — that belongs to `/task-done` after the done gate.

## Validation Expectations

- Run the narrowest focused validation immediately after the first substantive edit.
- Before handing off to `/task-done`, run `./scripts/validate-task.sh` from the repo root.
- The validation script runs backend lint, backend unit tests, backend integration tests, and frontend lint.
- For deployment or parity tasks, also run the narrowest task-specific environment check available.
- If the repo-wide validation fails because of pre-existing debt outside the task slice, record that explicitly and keep the task out of the done gate until resolved or consciously waived.

## Guardrails

- Do not widen scope after the first substantive edit without validation.
- Do not silently absorb adjacent task work.
- Do not update broad docs during implementation unless code would otherwise become misleading.

## Expected Output

Return:

1. The task implemented.
2. The files changed.
3. The focused validation run and result.
4. The result of `./scripts/validate-task.sh`.
5. Any remaining risk that `/task-done` must evaluate.
