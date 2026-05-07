---
name: spec-to-tasks
description: "Skill for converting an implementation-ready spec into an ordered task plan and live status tracker for this repository. Use when a new or updated spec needs to become actionable work in TASKS.md and TASK_STATUS.md, or when an existing task list must be expanded to cover newly groomed requirements."
---

# Spec To Tasks

Use this skill after `spec-groom` or whenever the repo already has a settled spec but lacks actionable tasks.

## Goal

Translate a spec into execution-ready tasks that are small enough for iterative implementation and validation.

## Read First

- The groomed spec source.
- `IFC.md`
- `ARCHITECTURE.md`
- `TASKS.md`
- `TASK_STATUS.md`
- `.github/copilot-instructions.md`

## Core Deliverables

Update or create:

1. `TASKS.md` as the stable implementation plan.
2. `TASK_STATUS.md` as the live completion snapshot.

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

## Planning Process

1. Map the spec delta to affected system areas.
2. Decide whether existing tasks already cover the change.
3. Add, split, or reorder tasks to preserve a clean dependency chain.
4. Add notes in `TASK_STATUS.md` describing the current repo reality, not aspirational work.
5. Ensure there is a sensible next task for `task-implement` to pick up.

## Guardrails

- Do not collapse a whole feature into one oversized task.
- Do not create task descriptions that depend on hidden context.
- Do not duplicate the same work across phases.
- Do not edit code as part of this skill unless it is required to keep planning docs consistent.

## Expected Final Response

Return:

1. The tasks created or updated.
2. The recommended next task.
3. Any dependency or sequencing notes.
4. A handoff to `task-implement`.
