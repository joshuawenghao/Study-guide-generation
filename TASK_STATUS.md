# Task Status

Last updated: 2026-05-05

This file mirrors the structure of `TASKS.md` and records the current repo state against each task directly.
Use it together with `TASKS.md`:

- `TASKS.md` = canonical implementation guide and task order
- `TASK_STATUS.md` = current completion state for each task in that guide

Status legend:

- `complete` = implemented and present in the repo
- `partial` = scaffolded or partially implemented, but not complete
- `not started` = missing or still placeholder-only

## Current snapshot

- Canonical backend root: `backend/study-guide-agent/`
- Legacy root-level backend code has been removed
- Backend scaffold, environment files, core type contracts, and eval fixture preservation are in place
- The workflow, prompts, validators, renderer, and frontend product UI are still largely unimplemented

## Phase 0 — Repository and tooling setup

### Task 0.1 — Confirm repository baseline

Status: `complete`
Notes: Root docs are present, the scaffolded backend exists, and the repository is organized around the current scaffolded layout.

### Task 0.2 — Verify the scaffolded backend project

Status: `complete`
Notes: `backend/study-guide-agent/` exists as the canonical scaffolded backend project and was previously validated with `agents-cli info`.

### Task 0.3 — Install backend dependencies and create environment files

Status: `complete`
Notes: `backend/study-guide-agent/.env.example` and local `backend/study-guide-agent/.env` exist. The backend environment location is now documented and standardized.

### Task 0.4 — Verify the frontend runtime

Status: `complete`
Notes: `frontend/` exists with the expected Next.js scaffold and local environment support.

### Task 0.5 — Verify evaluation assets and fixture roles

Status: `complete`
Notes: Both `backend/study-guide-agent/tests/eval/evalsets/` and `backend/study-guide-agent/tests/fixtures/legacy_evals/` exist, and their roles are documented.

## Phase 1 — Backend scaffold alignment

### Task 1.1 — Confirm the backend file tree exists in the scaffold

Status: `complete`
Notes: The expected `app/`, `tests/`, prompts, validators, renderer, and section directories exist under `backend/study-guide-agent/`.

### Task 1.2 — Align the scaffold’s shared Gemini wrapper

Status: `complete`
Notes: `backend/study-guide-agent/app/nodes/base.py` contains the shared Gemini wrapper and configuration constants.

### Task 1.3 — Align the scaffold entrypoint with the study-guide app identity

Status: `partial`
Notes: `app/agent.py` and `app/fast_api_app.py` have been aligned to the study-guide project identity, but the real study-guide workflow is not implemented yet.

## Phase 2 — Data contracts and type sync

### Task 2.1 — Implement backend data contracts

Status: `complete`
Notes: `backend/study-guide-agent/app/types.py` is implemented with the core study-guide contract models.

### Task 2.2 — Mirror the contract in the frontend

Status: `complete`
Notes: `frontend/lib/types.ts` exists and mirrors the current backend contract structure.

### Task 2.3 — Verify sync manually

Status: `partial`
Notes: Backend and frontend types are present, but there is no ongoing enforcement workflow beyond manual comparison.

## Phase 3 — System prompt and blueprint generation

### Task 3.1 — Implement the system prompt builder

Status: `not started`
Notes: `backend/study-guide-agent/app/prompts/system_prompt.py` is still placeholder-level.

### Task 3.2 — Implement the blueprint prompt template

Status: `not started`
Notes: A real blueprint prompt template has not been implemented yet.

### Task 3.3 — Implement the blueprint node

Status: `not started`
Notes: `backend/study-guide-agent/app/nodes/blueprint.py` is still a placeholder.

### Task 3.4 — Add a focused blueprint test

Status: `not started`
Notes: No dedicated blueprint test exists yet.

## Phase 4 — Section generation nodes

### Task 4.1 — Implement Wave 1 section prompt templates

Status: `not started`
Notes: Wave 1 prompt template files exist, but they are still placeholders.

### Task 4.2 — Implement Wave 1 section nodes

Status: `not started`
Notes: Wave 1 section node files exist, but they are still placeholders.

### Task 4.3 — Implement Wave 2 templates and nodes

Status: `not started`
Notes: Wave 2 templates and node implementations are still placeholder-only.

### Task 4.4 — Implement Wave 3 templates and nodes

Status: `not started`
Notes: Wave 3 templates and node implementations are still placeholder-only.

### Task 4.5 — Implement the answer key template and node

Status: `not started`
Notes: The answer key template and node are still placeholders.

### Task 4.6 — Add focused section-generation tests

Status: `not started`
Notes: No focused section-generation test suite exists yet.

## Phase 5 — Validation layer

### Task 5.1 — Implement hard validator: json_schema

Status: `not started`
Notes: The hard validator file exists, but the implementation is still placeholder-only.

### Task 5.2 — Implement hard validator: vocab_presence

Status: `not started`
Notes: `vocab_presence.py` is still a placeholder.

### Task 5.3 — Implement hard validator: self_assess_targets

Status: `not started`
Notes: `self_assess_targets.py` is still a placeholder.

### Task 5.4 — Implement hard validator: answer_key_quotes

Status: `not started`
Notes: `answer_key_quotes.py` is still a placeholder.

### Task 5.5 — Implement hard validator: passage_domain_diff

Status: `not started`
Notes: `passage_domain_diff.py` is still a placeholder.

### Task 5.6 — Implement soft validator: answer_leakage

Status: `not started`
Notes: `answer_leakage.py` is still a placeholder.

### Task 5.7 — Implement soft validator: reading_level

Status: `not started`
Notes: `reading_level.py` is still a placeholder.

### Task 5.8 — Implement the validator node

Status: `not started`
Notes: `backend/study-guide-agent/app/nodes/validator.py` is still a placeholder.

### Task 5.9 — Add validator tests

Status: `not started`
Notes: No validator-focused test suite exists yet.

## Phase 6 — Renderer and preview payload

### Task 6.1 — Implement the study guide HTML template

Status: `not started`
Notes: `backend/study-guide-agent/app/templates/study_guide.html.j2` is still placeholder-only.

### Task 6.2 — Implement the renderer node

Status: `not started`
Notes: `backend/study-guide-agent/app/nodes/renderer.py` is still a placeholder.

### Task 6.3 — Add renderer tests

Status: `not started`
Notes: No renderer test suite exists yet.

## Phase 7 — Workflow orchestration

### Task 7.1 — Implement the orchestrator workflow

Status: `partial`
Notes: `app/agent.py` exists, but it is still a minimal bootstrap rather than the full dynamic study-guide workflow.

### Task 7.2 — Add a focused backend-only integration check

Status: `not started`
Notes: No backend-only workflow integration check exists yet for the real product behavior.

## Phase 8 — Frontend shell and cleanup

### Task 8.1 — Remove default Next.js boilerplate

Status: `partial`
Notes: The frontend exists, but `frontend/app/page.tsx` is still default boilerplate rather than product UI.

### Task 8.2 — Implement global styles and app layout

Status: `partial`
Notes: `frontend/app/layout.tsx` and `frontend/app/globals.css` exist, but they have not been aligned to the intended product experience.

### Task 8.3 — Create empty component stubs

Status: `not started`
Notes: The expected frontend component stub files have not been created yet.

## Phase 9 — Teacher input form

### Task 9.1 — Implement InputForm.tsx

Status: `not started`
Notes: `InputForm.tsx` does not exist yet.

### Task 9.2 — Update page.tsx for form state

Status: `not started`
Notes: `frontend/app/page.tsx` does not yet manage study-guide request form state.

## Phase 10 — API proxy and streaming progress

### Task 10.1 — Implement the generate route

Status: `not started`
Notes: `frontend/app/api/generate/route.ts` does not exist yet.

### Task 10.2 — Implement ProgressTracker.tsx

Status: `not started`
Notes: `ProgressTracker.tsx` does not exist yet.

### Task 10.3 — Wire streaming into page.tsx

Status: `not started`
Notes: Page-level SSE handling is not implemented.

## Phase 11 — Results experience

### Task 11.1 — Implement PreviewSection.tsx

Status: `not started`
Notes: `PreviewSection.tsx` does not exist yet.

### Task 11.2 — Implement WebPreview.tsx

Status: `not started`
Notes: `WebPreview.tsx` does not exist yet.

### Task 11.3 — Implement DownloadButton.tsx

Status: `not started`
Notes: `DownloadButton.tsx` does not exist yet.

### Task 11.4 — Finish the results layout in page.tsx

Status: `not started`
Notes: `frontend/app/page.tsx` has no study-guide results experience yet.

## Phase 12 — End-to-end validation and QA

### Task 12.1 — Run the full app locally

Status: `not started`
Notes: No completed end-to-end local run has been recorded for the real study-guide flow.

### Task 12.2 — Run scaffold-native evals

Status: `not started`
Notes: The scaffold eval structure exists, but current study-guide behavior has not been validated through `agents-cli` eval runs.

### Task 12.3 — Run backend tests

Status: `partial`
Notes: Scaffold test structure exists, but the real study-guide implementation does not yet have matching backend test coverage.

### Task 12.4 — Verify IFC must-haves

Status: `not started`
Notes: Final IFC acceptance verification has not been completed.

## Guidance for future chats

- Read this file and `TASKS.md` together before starting new implementation work.
- Update the status of the exact matching task after implementation and a focused validation step.
- Build on `complete` tasks freely.
- Treat `partial` tasks as existing scaffolds that may need refactoring before extension.
