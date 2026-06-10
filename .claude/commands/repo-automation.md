---
description: "Workflow router for the delivery loop. Use when starting a new session, resuming work, deciding where to begin (new spec vs existing tasks vs docs catch-up), or routing between spec-groom, spec-to-tasks, task-implement, and docs-drift. Triggers on: 'where do I start', 'resume work', 'what should I do next', 'start a session', 'route the work'."
---

# Repo Automation

Workflow router for this repository. Use this at the start of a session to decide the correct starting path without skipping the repository control documents.

## Required Inputs

Read the following before routing:

- The user's latest request
- `IFC.md` when product scope or acceptance criteria might change
- `ARCHITECTURE.md` when the request changes design or contracts
- `DEPLOYMENT.md` when the request changes deployment topology or environment parity
- `TASKS.md` and `TASK_STATUS.md` before any implementation work
- `CLAUDE.md` for repo rules

## Decision Tree

### Path A — New Spec Needed

Choose when the user brings a net-new feature, a major requirement change, or a vague request not yet expressed in repo docs.

1. Confirm whether the request changes product scope, behavior, acceptance criteria, or architecture.
2. Read the most relevant control documents.
3. Use `/spec-groom`.
4. After the spec delta is accepted, use `/spec-to-tasks`.
5. Enter the implementation loop with `/task-implement`.

### Path B — Existing Spec, No Actionable Tasks Yet

Choose when requirements already exist in repo docs but no current task breakdown is ready.

1. Identify the authoritative spec documents.
2. Check whether the request is already covered by existing tasks.
3. If not, use `/spec-to-tasks`.
4. Enter the implementation loop with `/task-implement`.

### Path C — Tasks Already Exist

Choose when `TASKS.md` and `TASK_STATUS.md` already describe the next slice of work.

1. Read `TASKS.md` and `TASK_STATUS.md`.
2. Select the next `not started` task, or the smallest recoverable `partial` item.
3. Use `/task-implement`.

### Path D — Docs Are Behind Code

Choose when implementation happened but repo documents no longer reflect reality.

1. Read the shipped code and the affected docs.
2. Use `/docs-drift`.
3. Return to `/task-implement` only if additional code work remains.

## Implementation Loop Contract

Once tasks exist, the loop is:

1. `/task-implement`
2. `/task-done`
3. `/docs-drift`
4. Re-read `TASK_STATUS.md`
5. Repeat only if more work remains

## Guardrails

- Never start coding before reading `TASKS.md` and `TASK_STATUS.md` when task-driven work already exists.
- Never treat `TASKS.md` as the live progress log.
- Never mark a task complete without implementation plus at least one focused validation step.
- Never assume docs are current after code changes.
- Do not commit unless the user explicitly requests it.

## Expected Output

Produce a short routing decision:

1. The chosen path (A / B / C / D).
2. The reason that path applies.
3. The exact next command to use.
4. The concrete files that must be read before proceeding.
