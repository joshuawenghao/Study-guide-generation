---
description: "Turns a vague feature request, changed requirement, or stale design into an implementation-ready spec delta. Updates IFC.md and ARCHITECTURE.md. Use when requirements are unclear, new, or conflicting before task planning. Triggers on: 'new feature', 'groom the spec', 'refine requirements', 'spec is stale', 'what are we building'."
---

# Spec Groom

Use when repository requirements are not yet specific enough to plan or code safely. Turns a new feature request, changed requirement, stale design, or vague ask into an implementation-ready spec delta.

## Read First

Read all of these before producing output:

- `IFC.md`
- `ARCHITECTURE.md`
- `DEPLOYMENT.md` for deployment-related or environment-parity requirements
- `TASKS.md`
- `TASK_STATUS.md`
- `CLAUDE.md`

Read nearby implementation files only when they constrain feasibility.

## When To Use

- A feature request is new and not represented in repo docs.
- Existing docs conflict with current code or current business intent.
- A partially implemented feature exposes missing requirements.
- A stale spec needs to be refreshed before more coding.

## Required Outputs

Produce a groomed spec delta that covers:

1. Problem statement.
2. User-visible behavior.
3. Acceptance criteria.
4. Data contract impact.
5. Architecture impact.
6. Validation expectations.
7. Explicit out-of-scope items.

## Repository-Specific Rules

- Prefer updating `IFC.md` and `ARCHITECTURE.md` when the change belongs in the main product contract.
- Create a separate spec document only when the change is large enough that the main docs would become unclear.
- Keep `DEPLOYMENT.md` as the detailed deployment source of truth when the change is about environment topology, parity mode, secrets ownership, or release workflow.
- If types or API payloads will change, call that out explicitly for both backend and frontend.
- If the change affects section order, validators, or workflow orchestration, state that explicitly — those are tightly constrained in this repo.

## Grooming Process

1. Identify the smallest coherent feature or requirement delta.
2. Separate confirmed requirements from assumptions.
3. Convert vague goals into observable behavior and acceptance checks.
4. Identify every canonical document that must change.
5. Note open questions only when they block safe implementation.
6. If no blocker remains, produce a spec delta ready for `/spec-to-tasks`.

## Guardrails

- Do not jump into coding during grooming.
- Do not invent architecture that conflicts with current repo constraints.
- Do not leave acceptance criteria implicit.
- Do not update `TASKS.md` or `TASK_STATUS.md` until the spec delta is settled.

## Expected Output

Return:

1. A short summary of what changed.
2. The exact docs that should be edited.
3. Any blocking questions.
4. A clear handoff to `/spec-to-tasks` when the spec is implementation-ready.
