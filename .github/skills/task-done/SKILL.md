---
name: task-done
description: "Skill for deciding whether an implemented task slice is actually done in this repository. Use after task-implement to run the done gate, verify focused tests or checks, update TASK_STATUS.md, prepare review or commit handoff, and keep incomplete work marked partial when necessary."
---

# Task Done

Use this skill only after code for a single task slice exists.

## Goal

Determine whether the task is truly done, partially done, or still blocked, and update the live task tracker accordingly.

## Read First

- `TASKS.md`
- `TASK_STATUS.md`
- The files changed by `task-implement`
- Relevant tests, lint commands, or typecheck commands for the touched slice

## Done Gate

A task can be marked `complete` only if all of the following are true:

1. The planned behavior exists in code.
2. At least one focused validation step passed.
3. `./scripts/validate-task.sh` passed without unresolved failures.
4. The implementation does not obviously violate repo instructions or architecture constraints.
5. Any required paired updates, such as mirrored type changes, are present.
6. `TASK_STATUS.md` notes match reality.

If any item fails, mark the task `partial` or keep it `not started`, depending on actual state.

## Validation Workflow

1. Reuse the focused validation from `task-implement`.
2. Require a successful run of `./scripts/validate-task.sh` unless the user explicitly waives the done gate.
3. Record what was validated and what remains unverified.

## Repository-Specific Rules

- Update `TASK_STATUS.md` in the same turn when the task status changes.
- Do not edit `TASKS.md` unless the plan itself is now wrong.
- After the done gate passes, create a small git commit for the task slice.
- Stage only the files that belong to the completed task slice and related status/doc updates.
- Never include unrelated dirty files in the commit. If unrelated changes would be swept in, stop and ask the user how to proceed.
- Use the commit message format `task(<task-id>): <imperative summary>` when the task id is known, for example `task(4.1): implement wave 1 prompt templates`.
- If the work is a workflow or documentation slice without a task id, use `task: <imperative summary>`.

## Guardrails

- Do not mark work complete because it is mostly implemented.
- Do not hide missing tests or skipped validations.
- Do not use broad repo-wide test runs when a focused check is enough unless the task truly crosses those boundaries.

## Expected Final Response

Return:

1. The final task status decision.
2. The evidence supporting that decision.
3. The exact `TASK_STATUS.md` change made.
4. The commit created, or the blocker that prevented committing.
5. Whether the loop should continue to `docs-drift` or back to `task-implement`.
