---
name: repo-automation
description: "Workflow skill for deciding whether work in this repository should start from a new spec, an existing spec, or an existing task list. Use when the user wants to automate delivery flow, resume implementation, regroom stale requirements, continue from TASKS.md and TASK_STATUS.md, or decide which repo workflow skill to use next."
---

# Repo Automation

Use this skill as the workflow router for this repository.

## Goal

Choose the correct starting path for a coding session without skipping the repository control documents.

## Required Inputs

- The user's latest request.
- Current repository state.
- `IFC.md` when product scope or acceptance criteria might change.
- `ARCHITECTURE.md` when the request changes design or contracts.
- `TASKS.md` and `TASK_STATUS.md` before any implementation work.
- `.github/copilot-instructions.md` for repo rules.

## Decision Tree

### Path A: New Spec Needed

Choose this when the user brings a net-new feature, a major requirement change, or a vague request that is not yet expressed in the repo docs.

Actions:

1. Confirm whether the request changes product scope, behavior, acceptance criteria, or architecture.
2. Read the most relevant control documents.
3. Invoke or follow the `spec-groom` skill.
4. After the spec delta is accepted, invoke or follow the `spec-to-tasks` skill.
5. Enter the implementation loop with `task-implement`.

### Path B: Existing Spec, No Actionable Tasks Yet

Choose this when requirements already exist in repo docs, but no current task breakdown or task-status slice is ready.

Actions:

1. Identify the authoritative spec documents.
2. Check whether the request is already covered by existing tasks.
3. If not, invoke or follow `spec-to-tasks`.
4. Enter the implementation loop with `task-implement`.

### Path C: Tasks Already Exist

Choose this when `TASKS.md` and `TASK_STATUS.md` already describe the next slice of work.

Actions:

1. Read `TASKS.md` and `TASK_STATUS.md`.
2. Select the next task that is `not started` or the smallest recoverable `partial` item.
3. Invoke or follow `task-implement`.

### Path D: Docs Are Behind Code

Choose this when implementation happened but the repository documents no longer reflect reality.

Actions:

1. Read the shipped code and the affected docs.
2. Invoke or follow `docs-drift`.
3. Return to `task-implement` only if additional code work is still required.

## Implementation Loop Contract

Once tasks exist, the loop is:

1. `task-implement`
2. `task-done`
3. `docs-drift`
4. Re-read `TASK_STATUS.md`
5. Repeat only if more work remains

## Guardrails

- Never start coding before reading `TASKS.md` and `TASK_STATUS.md` when task-driven work already exists.
- Never treat `TASKS.md` as the live progress log.
- Never mark a task complete without implementation plus at least one focused validation step.
- Never assume docs are current after code changes; check them explicitly.
- Do not commit unless the user explicitly requests a commit.

## Expected Output

Produce a short routing decision with:

1. The chosen path.
2. The reason that path applies.
3. The exact next skill to use.
4. The concrete files that must be read before proceeding.
