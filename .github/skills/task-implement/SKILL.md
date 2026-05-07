---
name: task-implement
description: "Skill for implementing exactly one actionable task from TASKS.md and TASK_STATUS.md in this repository. Use when tasks already exist and the goal is to plan, code, and validate one task slice at a time without prematurely marking it done."
---

# Task Implement

Use this skill for the coding slice of the delivery loop.

## Goal

Take one concrete task from plan to implemented-with-focused-validation, while keeping scope narrow and reversible.

## Read First

- `TASKS.md`
- `TASK_STATUS.md`
- `.github/copilot-instructions.md`
- The nearest owning implementation files for the chosen task

## Task Selection Rules

- Prefer the next `not started` task.
- If the next relevant item is `partial`, resume the smallest unfinished slice.
- Do not pick multiple tasks in one pass unless the task definition itself is wrong and must be split.

## Execution Contract

1. State the exact task being implemented.
2. Identify the nearest code path that controls the behavior.
3. Form one falsifiable local hypothesis.
4. Make the smallest grounded edit that tests that hypothesis.
5. Run the narrowest focused validation available.
6. Repair locally if validation exposes a defect.
7. Stop when the task slice is implemented and validated enough for `task-done` to evaluate.

## Repository-Specific Rules

- Keep backend work inside `backend/study-guide-agent/`.
- Keep frontend work inside `frontend/`.
- When contract types change, update both backend and frontend types in the same implementation pass.
- Do not mark the task complete here; that belongs to `task-done` after the done gate.

## Validation Expectations

- Run the narrowest focused validation you can immediately after the first substantive edit.
- Before handing off to `task-done`, run the repository validation script at `./scripts/validate-task.sh` from the repo root.
- The repository validation script is expected to run backend lint, backend unit tests, backend integration tests, and frontend lint when those surfaces exist.
- If the repo-wide validation step fails because of pre-existing baseline debt outside the task slice, record that explicitly and keep the task out of the done gate until the failure is resolved or consciously waived.
- If commands are unavailable, explain the limitation and preserve a clear next validation step.

## Guardrails

- Do not widen scope after the first substantive edit without validation.
- Do not silently absorb adjacent task work.
- Do not update broad docs during implementation unless code would otherwise become misleading.

## Expected Final Response

Return:

1. The task implemented.
2. The files changed.
3. The focused validation run.
4. The result of `./scripts/validate-task.sh`.
5. Any remaining risk that `task-done` must evaluate next.
