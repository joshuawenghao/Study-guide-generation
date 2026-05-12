# Task Status

Last updated: 2026-05-12

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
- The backend now uses the project-local `backend/study-guide-agent/.venv` for ADK 2.0 beta work, with a narrow compatibility shim for the broken `google.adk.features` import surface in `google-adk==2.0.0b1`
- The system prompt builder, blueprint prompt template, blueprint node, and focused blueprint unit test are now implemented, and Wave 1 through Wave 3 plus the answer-key path now exist with focused unit coverage; the validator node now aggregates the json-schema, vocab-presence, self-assessment-target, answer-key-quote, and passage-domain hard validators plus the answer-leakage and reading-level soft validators, the study-guide HTML template and renderer node now produce PDF and ordered preview artifacts for validated section payloads, and the broader validator test surface now exercises the planned hard- and soft-validator cases in isolation while renderer-specific tests, workflow orchestration, and frontend product UI remain incomplete
- Deployment planning is now documented around a recommended Vercel frontend plus Cloud Run backend topology, with a separate local parity mode planned so production issues can be reproduced without changing the app architecture

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
Notes: `app/agent.py` and `app/fast_api_app.py` have been aligned to the study-guide project identity, and now load the repo-local ADK beta compatibility shim before ADK imports; the real study-guide workflow is still not implemented yet.

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

Status: `complete`
Notes: `backend/study-guide-agent/app/prompts/system_prompt.py` now builds a request-aware system prompt covering role, reading level, voice, cultural relevance, JSON-only formatting, and structured output discipline.

### Task 3.2 — Implement the blueprint prompt template

Status: `complete`
Notes: `backend/study-guide-agent/app/prompts/templates/blueprint.py` now builds a request-aware blueprint prompt with inline schema, essential-question guidance, vocabulary-count rules, learning-target instructions, and enforced topic-domain separation.

### Task 3.3 — Implement the blueprint node

Status: `complete`
Notes: `backend/study-guide-agent/app/nodes/blueprint.py` now builds system and blueprint prompts from a direct `GenerateRequest`, calls Gemini with `TEMP_BLUEPRINT`, parses JSON, validates the `Blueprint` model, and raises `RuntimeError` with raw response context on parse or schema failure.

### Task 3.4 — Add a focused blueprint test

Status: `complete`
Notes: `backend/study-guide-agent/tests/unit/test_blueprint.py` now covers the fixture-based blueprint path with a stubbed Gemini response, asserting required Blueprint fields, learning-target count, and distinct model versus assessment passage domains.

## Phase 4 — Section generation nodes

### Task 4.1 — Implement Wave 1 section prompt templates

Status: `complete`
Notes: `intro.py`, `learning_targets.py`, `warmup.py`, `vocabulary.py`, `key_points.py`, and `self_assessment.py` now build blueprint-driven prompts with inline JSON schemas and strict JSON-only return instructions; `tests/unit/test_wave1_prompt_templates.py` provides focused fixture-backed coverage for the template strings.

### Task 4.2 — Implement Wave 1 section nodes

Status: `complete`
Notes: `intro.py`, `learning_targets.py`, `warmup.py`, `vocabulary.py`, `key_points.py`, and `self_assessment.py` now build request-aware system prompts, call the shared Gemini wrapper with `TEMP_SECTION`, parse structured JSON payloads, and export ADK node wrappers using explicit `request` and `blueprint` arguments; `tests/unit/test_wave1_section_nodes.py` provides focused fixture-backed coverage for the shared generation path and malformed-JSON handling.

### Task 4.3 — Implement Wave 2 templates and nodes

Status: `complete`
Notes: `core_explainer.py`, `subconcept.py`, `strategy_list.py`, `deep_dive.py`, `model_passage.py`, and `assessment_passage.py` now build blueprint-aware prompts and request-aware section nodes; the shared section helper now supports section-specific `spec` inputs for `subconcept`, and `tests/unit/test_wave2_section_nodes.py` provides focused coverage for domain- and sub-competency-aware generation plus malformed-JSON handling.

### Task 4.4 — Implement Wave 3 templates and nodes

Status: `complete`
Notes: `check_in.py`, `assessment_questions.py`, and `step_up.py` now build dependency-aware prompts and request-aware section nodes that consume upstream structured payloads directly through explicit arguments and shared `spec` passing; `tests/unit/test_wave3_section_nodes.py` provides focused coverage for dependency-aware prompt generation and malformed-JSON handling.

### Task 4.5 — Implement the answer key template and node

Status: `complete`
Notes: `answer_key.py` now builds a dependency-aware prompt from `check_in`, `assessment_passage`, and `assessment_questions`, requiring quoted passage evidence inside assessment `possible_answer` fields; the answer-key node now uses `TEMP_ANSWER_KEY`, parses structured JSON, and `tests/unit/test_answer_key_node.py` provides focused coverage for shape and malformed-JSON handling.

### Task 4.6 — Add focused section-generation tests

Status: `complete`
Notes: `tests/unit/test_section_generation.py` now provides the dedicated representative section-generation slice from `TASKS.md` with fixture-based Blueprint input, narrow Wave 1 node coverage, a dependency-aware Wave 3 step-up test, and a shape-focused answer-key output test.

## Phase 5 — Validation layer

### Task 5.1 — Implement hard validator: json_schema

Status: `complete`
Notes: `backend/study-guide-agent/app/validators/hard/json_schema.py` now validates section payloads against backend Pydantic section models and returns `ValidationResult` failures instead of raising; focused unit coverage exists in `tests/unit/test_json_schema_validator.py`, and the repo done gate passed.

### Task 5.2 — Implement hard validator: vocab_presence

Status: `complete`
Notes: `backend/study-guide-agent/app/validators/hard/vocab_presence.py` now validates blueprint vocabulary coverage across combined body-section text, excludes the vocabulary section and answer key from the search corpus, and returns `ValidationResult` failures with per-section messages; focused coverage exists in `tests/unit/test_vocab_presence_validator.py`, and the repo done gate passed.

### Task 5.3 — Implement hard validator: self_assess_targets

Status: `complete`
Notes: `backend/study-guide-agent/app/validators/hard/self_assess_targets.py` now validates that each `self_assessment.rows[].skill` matches a blueprint learning-target objective verbatim and reports failures through `ValidationResult`; focused coverage exists in `tests/unit/test_self_assess_targets_validator.py`, and the repo done gate passed.

### Task 5.4 — Implement hard validator: answer_key_quotes

Status: `complete`
Notes: `backend/study-guide-agent/app/validators/hard/answer_key_quotes.py` now validates that each assessment answer in the answer key contains at least one quoted phrase and that at least one quoted phrase appears verbatim in the assessment passage body; focused coverage exists in `tests/unit/test_answer_key_quotes_validator.py`, and the repo done gate passed.

### Task 5.5 — Implement hard validator: passage_domain_diff

Status: `complete`
Notes: `backend/study-guide-agent/app/validators/hard/passage_domain_diff.py` now validates that blueprint `topic_domains.model_passage` and `topic_domains.assessment_passage` are both present and differ case-insensitively, failing the `assessment_passage` slice when they are equal or blank; focused coverage exists in `tests/unit/test_passage_domain_diff_validator.py`, and the repo done gate passed.

### Task 5.6 — Implement soft validator: answer_leakage

Status: `complete`
Notes: `backend/study-guide-agent/app/validators/soft/answer_leakage.py` now extracts quoted evidence phrases from assessment answer-key `possible_answer` fields, ignores `assessment_passage` and `answer_key`, and emits non-blocking `ValidationResult.warnings` when other sections repeat those phrases; focused coverage exists in `tests/unit/test_answer_leakage_validator.py`, and the repo done gate passed.

### Task 5.7 — Implement soft validator: reading_level

Status: `complete`
Notes: `backend/study-guide-agent/app/validators/soft/reading_level.py` now computes section-level Flesch-Kincaid scores with `textstat`, compares them to an explicit target grade level using a ±1.0 band, and emits non-blocking `ValidationResult.warnings` for out-of-band sections; focused coverage exists in `tests/unit/test_reading_level_validator.py`, `textstat` was added to backend dependencies, and the repo done gate passed.

### Task 5.8 — Implement the validator node

Status: `complete`
Notes: `backend/study-guide-agent/app/nodes/validator.py` now aggregates all implemented hard and soft validators into one `ValidationResult`, runs json-schema validation across all provided section payloads including repeated `subconcept` entries, skips content-model validators when schema validation already failed for that slice, and exposes an ADK node wrapper; focused coverage exists in `tests/unit/test_validator_node.py`, and the repo done gate passed.

### Task 5.9 — Add validator tests

Status: `complete`
Notes: Broader validator-focused coverage now exists across `tests/unit/test_json_schema_validator.py`, `tests/unit/test_vocab_presence_validator.py`, `tests/unit/test_self_assess_targets_validator.py`, `tests/unit/test_answer_key_quotes_validator.py`, `tests/unit/test_passage_domain_diff_validator.py`, `tests/unit/test_answer_leakage_validator.py`, `tests/unit/test_reading_level_validator.py`, and `tests/unit/test_validator_node.py`; the planned passing, failing, and warning-only validator cases are executable in isolation, and the repo done gate passed.

## Phase 6 — Renderer and preview payload

### Task 6.1 — Implement the study guide HTML template

Status: `complete`
Notes: `backend/study-guide-agent/app/templates/study_guide.html.j2` now defines the canonical study-guide PDF layout in Jinja2 with explicit section ordering, vocabulary and self-assessment tables, validation warning callouts, and page breaks for the assessment passage and answer key; focused Jinja parse validation and `./scripts/validate-task.sh` both passed.

### Task 6.2 — Implement the renderer node

Status: `complete`
Notes: `backend/study-guide-agent/app/nodes/renderer.py` now accepts explicit `blueprint`, `sections`, and `validation` inputs, renders `app/templates/study_guide.html.j2` through Jinja2, converts HTML to PDF with WeasyPrint, base64-encodes the PDF bytes, and returns a `GenerateResponse` with a canonical-order `WebPreviewPayload`; focused renderer smoke validation plus backend lint, backend Pyright, backend tests, and frontend lint all passed.

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

## Phase 13 — Deployment and parity

### Task 13.1 — Document the deployment topology and environment matrix

Status: `complete`
Notes: `DEPLOYMENT.md` now exists at the repo root and aligns the deployment plan across `IFC.md`, `ARCHITECTURE.md`, `TASKS.md`, and the repo README files around fast local dev, local parity, remote dev, and production.

### Task 13.2 — Containerize the backend for Cloud Run parity

Status: `partial`
Notes: The backend already includes a Dockerfile, but Cloud Run suitability and local parity expectations have not been validated end to end yet.

### Task 13.3 — Add a local parity orchestration path

Status: `not started`
Notes: There is no documented single-command parity stack yet for a production-mode frontend plus Cloud Run-style backend runtime.

### Task 13.4 — Configure the backend deployment for Cloud Run

Status: `not started`
Notes: The backend README mentions `agents-cli deploy`, but repo-specific Cloud Run environment, CORS, and service configuration are not implemented or verified yet.

### Task 13.5 — Configure the frontend deployment for Vercel

Status: `not started`
Notes: The repo now recommends Vercel for the frontend, but preview and production environment configuration have not been set up or validated yet.

### Task 13.6 — Run staged deployment checkpoints

Status: `not started`
Notes: No remote deployment checkpoints have been recorded yet after Phases 7, 10, or 12.

## Guidance for future chats

- Read this file and `TASKS.md` together before starting new implementation work.
- Update the status of the exact matching task after implementation and a focused validation step.
- Build on `complete` tasks freely.
- Treat `partial` tasks as existing scaffolds that may need refactoring before extension.
