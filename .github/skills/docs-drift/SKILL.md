---
name: docs-drift
description: "Skill for reconciling repository documentation with shipped code after implementation work. Use when README, IFC.md, ARCHITECTURE.md, TASK_STATUS.md, task notes, or other references have drifted from the current codebase, or when a coding session finished and the docs need to catch up."
---

# Docs Drift

Use this skill after `task-done` or whenever the repo documentation no longer reflects the actual implementation.

## Goal

Bring the control documents and supporting docs back into alignment with shipped code.

The primary live shipped-state document for this repository is `CODEBASE_STATE.md` at the repo root.

## Read First

- `TASK_STATUS.md`
- `TASKS.md`
- `CODEBASE_STATE.md`
- `.github/copilot-instructions.md`
- The changed code files
- The most relevant docs among `README.md`, `IFC.md`, `ARCHITECTURE.md`, backend README files, and any feature-specific spec docs

## Reconciliation Process

1. Identify behavior or structure that changed in code.
2. Identify which documents claim something different, or omit the new reality.
3. Update `CODEBASE_STATE.md` so it describes the shipped code in plain language.
4. Update only the additional docs needed to restore an accurate mental model.
5. Prefer factual statements about current behavior over aspirational roadmap language.
6. Keep `TASK_STATUS.md` as the live implementation snapshot.

## Repository-Specific Priorities

- Update `TASK_STATUS.md` whenever implementation status changed.
- Update `CODEBASE_STATE.md` on every docs-drift pass that changes shipped behavior, validation surfaces, automation workflow, or developer-facing capabilities.
- Keep `CODEBASE_STATE.md` in a stable section layout so readers can compare updates over time.
- Update `TASKS.md` only if the execution plan is now inaccurate.
- Update `ARCHITECTURE.md` when design, data flow, or contracts changed.
- Update `README.md` when setup, usage, or repo workflow changed.

## Guardrails

- Do not rewrite docs broadly when a small delta is enough.
- Do not backfill documentation for features that do not exist yet.
- Do not leave stale examples or outdated command paths behind.

## Expected Final Response

Return:

1. Which docs were updated.
2. What drift was corrected.
3. The `CODEBASE_STATE.md` sections refreshed.
4. Any remaining documentation debt.
5. Whether the workflow should loop back to `task-implement` or stop.
