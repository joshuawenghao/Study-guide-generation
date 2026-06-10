---
description: "Converts a settled spec into execution-ready entries in TASKS.md and TASK_STATUS.md. Use after spec-groom or when requirements exist but no task breakdown yet. Triggers on: 'break into tasks', 'create tasks', 'plan the work', 'update TASKS.md', 'task breakdown'."
---

# Spec To Tasks

Use after `/spec-groom` — or whenever the repo has a settled spec but lacks actionable tasks. Translates a spec into execution-ready tasks in `TASKS.md` and `TASK_STATUS.md`.

## Read First

- The groomed spec source
- `IFC.md`
- `ARCHITECTURE.md`
- `DEPLOYMENT.md` when deployment or parity work is in scope
- `TASKS.md`
- `TASK_STATUS.md`
- `CLAUDE.md`

## Core Deliverables

Update or create:

1. `TASKS.md` — stable implementation plan.
2. `TASK_STATUS.md` — live completion snapshot.

## Task Design Rules

- Each task must describe one meaningful slice of behavior.
- Each task must have a clear done condition.
- Each task should suggest the narrowest useful validation step.
- Tasks should follow repository architecture boundaries rather than arbitrary file groupings.
- If backend and frontend contract changes are coupled, the task must say so explicitly.

## Repository-Specific Rules

- Keep `TASKS.md` stable and instructional.
- Keep `TASK_STATUS.md` mutable and factual.
- Use `complete`, `partial`, and `not started` consistently.
- Do not mark anything `complete` while planning.
- Prefer inserting new tasks into the existing phase structure unless a new phase is clearly required.
- When deployment work is cross-cutting, allow checkpoint tasks to reference readiness in earlier phases instead of forcing all deployment work to the very end.

## Planning Process

1. Map the spec delta to affected system areas.
2. Decide whether existing tasks already cover the change.
3. Add, split, or reorder tasks to preserve a clean dependency chain.
4. Add notes in `TASK_STATUS.md` describing current repo reality, not aspirational work.
5. Ensure there is a sensible next task for `/task-implement` to pick up.

## Guardrails

- Do not collapse a whole feature into one oversized task.
- Do not create task descriptions that depend on hidden context.
- Do not duplicate the same work across phases.
- Do not edit code as part of this command unless required to keep planning docs consistent.

## Expected Output

Return:

1. The tasks created or updated.
2. The recommended next task.
3. Any dependency or sequencing notes.
4. A handoff to `/task-implement`.
