# Task Status

Last updated: 2026-05-28

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
- The system prompt builder, blueprint prompt template, blueprint node, and focused blueprint unit test are now implemented, and Wave 1 through Wave 3 plus the answer-key path now exist with focused unit coverage; the validator node now aggregates the json-schema, vocab-presence, self-assessment-target, answer-key-quote, assessment-question-grounding, and passage-domain hard validators plus the answer-leakage and reading-level soft validators, Phase 6 now includes the study-guide HTML template, renderer node, and focused renderer tests for preview ordering and PDF artifact shape, and Phase 7 now includes both the exported ADK workflow in `app/agent.py` and a focused backend-only integration test that exercises orchestration, dependency wiring, retry, and render handoff; Phase 9 is now in place with a controlled teacher input form and page-level form-stage state, and Phase 10 now includes a backend `/generate` SSE surface, a thin Next.js `/api/generate` proxy, a dedicated `ProgressTracker` component, and page-level SSE handling in `frontend/app/page.tsx`, while Phase 11 now adds a complete preview, download, and results-layout experience in the frontend
- The backend now strips HTML-like markup from model-returned section strings before validation, preview emission, and PDF rendering, auto-repairs missing assessment-answer quote embedding when Gemini only fills `evidence_quote`, and reports reading-level warnings as explicit above-versus-below grade-band messages with extra tolerance for slightly simpler upper-secondary technical prose
- The answer-key path now derives an exact quote bank from the assessment passage, realigns assessment answers back to the upstream assessment-question metadata during normalization, and applies that same normalization on answer-key retries so quote handling is less dependent on raw model phrasing
- The backend now also grounds `assessment_questions` evidence requirements to exact passage quotes before downstream use, hard-validates that grounding against the assessment passage, and defensively re-normalizes `answer_key` during validation and rendering so raw model assessment answers cannot silently bypass the quote guard
- The shared section parser now also strips malformed inline quoted-list annotations, multiline placeholder blocks, and code-like bracket annotations built from concatenated quoted fragments before a second parse attempt, and the assessment-passage prompt now explicitly forbids those bracketed or code-like placeholder annotations inside passage paragraphs, closing the live UI parse failure that had been observed in `assessment_passage`
- The PDF renderer no longer includes validation warnings in the teacher-facing study guide PDF, keeping those warnings internal to backend validation data and the frontend review workspace rather than the final downloadable artifact
- The answer-key path now also grounds `check_in_answers` on the `model_passage` text, realigns check-in answer metadata back to the upstream `check_in.questions`, and prefers exact question-text matching over model-supplied numbering when those disagree
- The answer-key path now also hard-validates `check_in_answers.evidence_quote` against the `model_passage`, normalizes non-verbatim check-in evidence back to a single verbatim model-passage sentence during generation, validation, retry, and rendering, and closes the fresh nursing run failure where `answer_key` had fallen into failed/best-effort state
- The check-in answer realignment path now also assigns each raw model answer at most once and scores unmatched entries against the upstream question text plus evidence hint instead of over-trusting returned numbering, which closes the nursing run bug where check-in answers 2 and 3 could cross when the model drifted
- The answer-key prompt now also gives check-in answers their own verbatim model-passage quote bank and requires one question-specific `evidence_quote` per entry, reducing generic quote reuse across adjacent check-in answers in live nursing runs
- The shared section parser now also strips additional malformed `assessment_passage` placeholder variants seen in live nursing runs, including unmatched mixed-quote concatenation prefixes, escaped-quote bracket annotations, adjacent escaped-string placeholder annotations, and parsed string-level placeholder remnants that survive valid JSON decoding
- The shared section parser now also performs a late-fallback repair for malformed unmatched quote-concatenation prefixes such as `["] + ["]` patterns in `assessment_passage` payloads, plus parsed-string cleanup for `["] + ["]` remnants that survive valid JSON decoding; focused wave-2 parser coverage now includes this nursing-shaped regression case
- Fresh full browser reruns now pass for both the teacher page (`/`) and the prompt-lab nursing stress flow (`/prompt-lab`) with multiple section overrides, and the prior `assessment_passage` parse failure is no longer reproduced
- The shared section parser now also strips doubled-quote bracket placeholder fragments such as `[""quote""]` and repairs malformed model JSON with mismatched closing braces and brackets before retrying parse, closing additional live generation failures seen in nursing runs
- The PDF icon renderer now inlines SVG stroke/fill attributes directly in the Jinja template and replaces the tiny point-style dot glyph hacks used by a few icons, so downloaded PDFs render the new header and callout icon set more cleanly under WeasyPrint instead of collapsing some closed shapes into black blobs
- Deployment planning is now documented around a recommended Vercel frontend plus Cloud Run backend topology, with a separate local parity mode planned so production issues can be reproduced without changing the app architecture; the backend container now honors the runtime `PORT` environment variable, serves `app.fast_api_app:app` in the same image shape intended for Cloud Run, and now includes environment-driven CORS/runtime config plus a standardized Cloud Run deploy entrypoint in `DEPLOYMENT.md` and `scripts/deploy-backend-cloud-run.sh`
- `IFC.md` and `ARCHITECTURE.md` now also document a new deterministic iconography requirement for section headers, selected subheaders, and repeated callouts; the shared preview contract in `backend/study-guide-agent/app/types.py` and `frontend/lib/types.ts` now carries optional `icon_key` metadata, the backend renderer now emits deterministic section icon keys, the PDF template now renders inline SVG icons for section headers plus repeated callouts using a more literal section-specific icon family, the focused renderer tests now assert both preview `icon_key` emission and a stable PDF render path with icon markup present, and the frontend web preview now maps the same icon family onto section headers plus repeated warning, success, and default callout treatments
- `IFC.md` and `ARCHITECTURE.md` now also define a prompt-lab MVP for non-technical remote reviewers, including a private reviewer-only page, a request-scoped `PromptLabGenerateRequest` contract, dedicated proxy routing, and explicit MVP boundaries; the shipped code now includes the contract surface, backend runtime prompt-override layer, dedicated backend prompt-lab SSE and sample endpoints, matching thin Next.js prompt-lab proxy routes, and a checked-in curated sample catalog with five reviewer cases across English, Mathematics, Nursing/Health, Science, and Social Studies, while the reviewer UI itself remains unimplemented
- `IFC.md` and `ARCHITECTURE.md` now also define a prompt-lab MVP for non-technical remote reviewers, including a private reviewer-only page, a request-scoped `PromptLabGenerateRequest` contract, dedicated proxy routing, and explicit MVP boundaries; the shipped code now includes the contract surface, backend runtime prompt-override layer, dedicated backend prompt-lab SSE and sample endpoints, matching thin Next.js prompt-lab proxy routes, a checked-in curated sample catalog with five reviewer cases across English, Mathematics, Nursing/Health, Science, and Social Studies, and a private reviewer page at `frontend/app/prompt-lab/page.tsx` with sample loading plus prompt editors
- Phase 14.1 is now implemented: `backend/study-guide-agent/app/types.py` and `frontend/lib/types.ts` both define the prompt-lab request contract, explicit supported section override allowlists, stable sample-case identifiers, and a shared sample-input model, while `backend/study-guide-agent/tests/unit/test_prompt_lab_types.py` now proves that supported override keys validate and unsupported keys or unknown sample ids fail clearly
- Phase 14.2 is now implemented: `backend/study-guide-agent/app/prompts/runtime.py` now centralizes prompt-lab request unwrapping, system-prompt append handling, and section-specific override injection; the shared section helper, blueprint node, answer-key node, and retry path in `backend/study-guide-agent/app/agent.py` now all route through that runtime layer so supported overrides apply without editing the base prompt template files, and `backend/study-guide-agent/tests/unit/test_prompt_lab_prompt_overrides.py` now proves intro, blueprint, and answer-key override behavior

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

Status: `complete`
Notes: `app/agent.py` and `app/fast_api_app.py` are aligned to the study-guide project identity, load the repo-local ADK beta compatibility shim before ADK imports, and now expose the real study-guide workflow entrypoint rather than the sample bootstrap.

## Phase 2 — Data contracts and type sync

### Task 2.1 — Implement backend data contracts

Status: `complete`
Notes: `backend/study-guide-agent/app/types.py` is implemented with the core study-guide contract models.

### Task 2.2 — Mirror the contract in the frontend

Status: `complete`
Notes: `frontend/lib/types.ts` exists and mirrors the current backend contract structure.

### Task 2.3 — Verify sync manually

Status: `complete`
Notes: The manual contract-sync check now matches the current repo state: the request/response contract in `backend/study-guide-agent/app/types.py` and `frontend/lib/types.ts` is still aligned for `GenerateRequest`, `Blueprint`, `WebPreviewPayload`, `ValidationResult`, `GenerateResponse`, and `ProgressEvent`, and the frontend proxy continues to consume the shared request shape through `frontend/app/api/generate/route.ts`. There is still no automated cross-runtime drift enforcement beyond manual comparison, but the manual verification task itself is complete.

### Task 2.4 — Extend the preview contract for iconography

Status: `complete`
Notes: `backend/study-guide-agent/app/types.py` and `frontend/lib/types.ts` now both expose optional presentation-only `icon_key` metadata on `PreviewSection` without changing the request contract or making icon data required. Focused validation passed with `cd backend/study-guide-agent && uv run pyright app` and `cd frontend && npm run typecheck`, and the repo done gate `./scripts/validate-task.sh` also passed.

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
Notes: `backend/study-guide-agent/app/validators/soft/answer_leakage.py` now extracts quoted evidence phrases from assessment answer-key `possible_answer` fields, ignores `assessment_passage`, `assessment_questions`, and `answer_key`, and emits non-blocking `ValidationResult.warnings` when instructional sections repeat those phrases; focused coverage exists in `tests/unit/test_answer_leakage_validator.py`, and the repo done gate passed.

### Task 5.7 — Implement soft validator: reading_level

Status: `complete`
Notes: `backend/study-guide-agent/app/validators/soft/reading_level.py` now computes section-level Flesch-Kincaid scores with `textstat`, focuses on longer prose-heavy sections, and emits non-blocking `ValidationResult.warnings` when a section is materially above or below the target grade band using the current asymmetric tolerance rules; focused coverage exists in `tests/unit/test_reading_level_validator.py`, `textstat` was added to backend dependencies, and the repo done gate passed.

### Task 5.8 — Implement the validator node

Status: `complete`
Notes: `backend/study-guide-agent/app/nodes/validator.py` now aggregates all implemented hard and soft validators into one `ValidationResult`, runs json-schema validation across all provided section payloads including repeated `subconcept` entries, skips content-model validators when schema validation already failed for that slice, and exposes an ADK node wrapper; focused coverage exists in `tests/unit/test_validator_node.py`, and the repo done gate passed.

### Task 5.9 — Add validator tests

Status: `complete`
Notes: Broader validator-focused coverage now exists across `tests/unit/test_json_schema_validator.py`, `tests/unit/test_vocab_presence_validator.py`, `tests/unit/test_self_assess_targets_validator.py`, `tests/unit/test_answer_key_quotes_validator.py`, `tests/unit/test_passage_domain_diff_validator.py`, `tests/unit/test_answer_leakage_validator.py`, `tests/unit/test_reading_level_validator.py`, and `tests/unit/test_validator_node.py`; the planned passing, failing, and warning-only validator cases are executable in isolation, and the repo done gate passed.

## Phase 6 — Renderer and preview payload

### Task 6.1 — Implement the study guide HTML template

Status: `complete`
Notes: `backend/study-guide-agent/app/templates/study_guide.html.j2` now defines the canonical study-guide PDF layout in Jinja2 with explicit section ordering, vocabulary and self-assessment tables, and page breaks for the assessment passage and answer key; validation warnings are intentionally omitted from the teacher-facing PDF and remain available only through backend validation data plus the frontend review workspace. Focused Jinja parse validation and `./scripts/validate-task.sh` both passed.

### Task 6.2 — Implement the renderer node

Status: `complete`
Notes: `backend/study-guide-agent/app/nodes/renderer.py` now accepts explicit `blueprint`, `sections`, and `validation` inputs, renders `app/templates/study_guide.html.j2` through Jinja2, converts HTML to PDF with WeasyPrint, base64-encodes the PDF bytes, and returns a `GenerateResponse` with a canonical-order `WebPreviewPayload`; focused renderer smoke validation plus backend lint, backend Pyright, backend tests, and frontend lint all passed.

### Task 6.3 — Add renderer tests

Status: `complete`
Notes: `backend/study-guide-agent/tests/unit/test_renderer.py` now provides focused executable coverage for the renderer path, asserting that the rendered PDF payload decodes to bytes with a PDF header and that preview sections are emitted in canonical order; the focused renderer test module and `./scripts/validate-task.sh` both passed.

### Task 6.4 — Add deterministic iconography to the renderer and PDF template

Status: `complete`
Notes: `backend/study-guide-agent/app/nodes/renderer.py` now owns a deterministic icon allowlist for preview sections and passes section/UI icon context into the PDF template, while `backend/study-guide-agent/app/templates/study_guide.html.j2` now renders inline SVG icons for section headers and repeated callout variants with text-only fallback for unsupported keys. Focused validation passed with `cd backend/study-guide-agent && uv run pytest tests/unit/test_renderer.py -q`, and the repo done gate `./scripts/validate-task.sh` also passed.
Update: The shipped icon family was later refreshed to use more descriptive section-specific shapes such as a compass for learning targets, a gamepad for warmup, stacked books for vocabulary, a reader icon for core explainer, notes for passages, and a pencil for assessment questions while keeping the same deterministic `icon_key` flow and graceful fallback behavior.

### Task 6.5 — Add focused renderer iconography tests

Status: `complete`
Notes: `backend/study-guide-agent/tests/unit/test_renderer.py` now asserts preview `icon_key` emission for canonical preview entries and verifies that the HTML handed to the PDF render path still includes inline SVG icon markup for both section headings and callouts. Focused validation passed with `cd backend/study-guide-agent && uv run pytest tests/unit/test_renderer.py -q`, and the repo done gate `./scripts/validate-task.sh` also passed.

## Phase 7 — Workflow orchestration

### Task 7.1 — Implement the orchestrator workflow

Status: `complete`
Notes: `app/agent.py` now exports the real ADK workflow entrypoint: blueprint generation runs first, Wave 1 and Wave 2 use `asyncio.gather()`, Wave 3 uses explicit dependency inputs, answer-key generation runs last, validation triggers a one-pass retry loop with failure-specific retry prompts at `TEMP_RETRY`, and rendering returns the final `GenerateResponse`; the repo done gate passed after focused workflow import, Pyright, and backend integration smoke validation.

### Task 7.2 — Add a focused backend-only integration check

Status: `complete`
Notes: `backend/study-guide-agent/tests/integration/test_agent.py` now includes a focused backend-only workflow integration test that runs the real orchestrator function through a fake ADK context, stubs the section generators, validation, retry Gemini call, and renderer, and verifies workflow order, dependency wiring, one-pass retry behavior, and render completion; the repo done gate passed.

## Phase 8 — Frontend shell and cleanup

### Task 8.1 — Remove default Next.js boilerplate

Status: `complete`
Notes: `frontend/app/page.tsx` now removes the default Create Next App landing page in favor of a minimal study-guide product placeholder, and `frontend/components/` now exists so subsequent UI tasks have a stable home; `cd frontend && npm run lint` and `./scripts/validate-task.sh` both passed.

### Task 8.2 — Implement global styles and app layout

Status: `complete`
Notes: `frontend/app/layout.tsx` now defines study-guide product metadata plus a teacher-facing top shell, `frontend/app/globals.css` now sets the shared canvas, typography, and surface tokens for the app, and `frontend/app/page.tsx` was aligned to that shell; `cd frontend && npm run lint` and `./scripts/validate-task.sh` both passed.

### Task 8.3 — Create empty component stubs

Status: `complete`
Notes: The frontend component structure now exists with stub exports for `InputForm`, `ProgressTracker`, `WebPreview`, `DownloadButton`, and `PreviewSection` under `frontend/components/`; `cd frontend && npm run lint` and `./scripts/validate-task.sh` both passed.

## Phase 9 — Teacher input form

### Task 9.1 — Implement InputForm.tsx

Status: `complete`
Notes: `frontend/components/InputForm.tsx` is now a fully controlled client component that emits a validated `GenerateRequest`, includes grouped lesson/curriculum/instructional-design/optional sections, supports dynamic sub-competency rows, prevents default form submission, and passed focused frontend lint plus `./scripts/validate-task.sh`.

### Task 9.2 — Update page.tsx for form state

Status: `complete`
Notes: `frontend/app/page.tsx` now manages `GenerationStage`, page-level error state, and staged `GenerateRequest` handoff for the form flow; it renders `InputForm` in the idle state, shows a request-staged summary for the planning state, and passed focused frontend lint plus `./scripts/validate-task.sh`.

## Phase 10 — API proxy and streaming progress

### Task 10.1 — Implement the generate route

Status: `complete`
Notes: `frontend/app/api/generate/route.ts` now exists as a thin SSE proxy that forwards typed `GenerateRequest` payloads to the backend `POST /generate` endpoint configured by `ADK_BACKEND_URL`, preserves streamed SSE events, and normalizes transport failures into SSE error events; `backend/study-guide-agent/app/fast_api_app.py` now also exposes the typed `/generate` compatibility endpoint for the frontend route, focused backend streaming coverage exists in `backend/study-guide-agent/tests/integration/test_server_e2e.py`, and `./scripts/validate-task.sh` passed.

### Task 10.2 — Implement ProgressTracker.tsx

Status: `complete`
Notes: `frontend/components/ProgressTracker.tsx` now renders a dedicated step-based workflow tracker driven by `GenerationStage`, streamed `ProgressEvent[]`, and elapsed time; the component clearly separates blueprint, section generation, validation, retry, render, and done states, `frontend/lib/types.ts` now exports the shared `ProgressTrackerProps` contract, and `./scripts/validate-task.sh` passed.

### Task 10.3 — Wire streaming into page.tsx

Status: `complete`
Notes: `frontend/app/page.tsx` now posts the staged `GenerateRequest` to `/api/generate`, parses streamed SSE `progress`, `result`, and `error` events, tracks `ProgressEvent[]`, elapsed time, and the final `GenerateResponse`, drives `GenerationStage` transitions for generating, validating, rendering, done, and error states, and integrates `ProgressTracker` into the live page flow; `./scripts/validate-task.sh` passed.

## Phase 11 — Results experience

### Task 11.1 — Implement PreviewSection.tsx

Status: `complete`
Notes: `frontend/components/PreviewSection.tsx` now renders typed preview payloads with tailored layouts for learning targets, vocabulary, model and assessment passages, self-assessment, and answer-key sections, while also surfacing per-section validation failures and best-effort indicators; `cd frontend && npm run typecheck`, `cd frontend && npm run lint`, and `./scripts/validate-task.sh` passed.

### Task 11.2 — Implement WebPreview.tsx

Status: `complete`
Notes: `frontend/components/WebPreview.tsx` now accepts `WebPreviewPayload` and `ValidationResult`, renders preview sections in backend-provided order through `PreviewSection`, and surfaces a clear validation summary plus warning callouts; `cd frontend && npm run typecheck`, `cd frontend && npm run lint`, and `./scripts/validate-task.sh` passed.

### Task 11.3 — Implement DownloadButton.tsx

Status: `complete`
Notes: `frontend/components/DownloadButton.tsx` now accepts base64 PDF data and a filename, decodes the PDF in the browser, and triggers a reliable client-side file download with simple error feedback when the payload is missing or invalid; `cd frontend && npm run typecheck`, `cd frontend && npm run lint`, and `./scripts/validate-task.sh` passed.

### Task 11.4 — Finish the results layout in page.tsx

Status: `complete`
Notes: `frontend/app/page.tsx` now keeps `ProgressTracker` visible after completion, renders a responsive results workspace with preview and download tabs, surfaces validation warnings in the completed state, and wires the final `GenerateResponse` into `WebPreview` plus `DownloadButton`; `cd frontend && npm run typecheck`, `cd frontend && npm run lint`, and `./scripts/validate-task.sh` passed.

### Task 11.5 — Add iconography parity to the web preview

Status: `complete`
Notes: `frontend/components/PreviewIcon.tsx` now provides a local inline SVG icon mapping for the renderer-owned `icon_key` values and recurring callout roles, while `frontend/components/PreviewSection.tsx` and `frontend/components/WebPreview.tsx` now render those icons on section headers plus repeated warning, success, and default callout treatments with graceful text-only fallback when icon metadata is missing or unknown. Focused validation passed with `cd frontend && npm run typecheck`, and the repo done gate `./scripts/validate-task.sh` also passed.

## Phase 12 — End-to-end validation and QA

### Task 12.1 — Run the full app locally

Status: `complete`
Notes: The real local stack now completes repeated end-to-end UI runs: Grade 6 English, Grade 8 Science, Grade 7 Mathematics, and Grade 12 Health/Nursing all reached `Results ready` with 0 failed sections and 0 best-effort sections in the browser UI, leaving only soft reading-level warnings across those live runs. `frontend/app/page.tsx` no longer aborts the generation request on its own stage transitions, `backend/study-guide-agent/app/app_utils/weasyprint_compat.py` now teaches local macOS runs how to resolve Homebrew WeasyPrint libraries before renderer import, and the shared section parser plus `assessment_passage` prompt now also guard against malformed inline clue lists, multiline placeholder blocks, and code-like concatenation annotations that had caused live `assessment_passage` parse failures. `./scripts/validate-task.sh` passed after the relevant validation slices.

### Task 12.2 — Run scaffold-native evals

Status: `complete`
Notes: Scaffold-native CLI and eval loading now use a cleaner separation: the conversational surface lives under `backend/study-guide-agent/eval_app/`, the repo-local `backend/study-guide-agent/agents-cli` wrapper routes local `run` and `eval run` commands to that eval app, and `backend/study-guide-agent/app/` is back to being the real workflow implementation package used by `/generate`. `backend/study-guide-agent/tests/eval/evalsets/basic.evalset.json` now targets `eval_app`, `./agents-cli eval run` still passes with 2 tests passed and 0 failed after the cleanup, and `./scripts/validate-task.sh` passed.

### Task 12.3 — Run backend tests

Status: `complete`
Notes: The real backend test suite now runs cleanly from `backend/study-guide-agent/` with `uv run pytest tests/unit tests/integration`, covering the implemented workflow, validators, renderer, section nodes, prompt templates, FastAPI boot path, and orchestrator retry flow. The current backend suite passes at 79 tests passed and 0 failed, and `./scripts/validate-task.sh` also passed afterward.

### Task 12.4 — Verify IFC must-haves

Status: `complete`
Notes: The IFC must-have checklist has now been verified against passing local validations, the shipped control paths, and fresh live browser demos. `./scripts/validate-task.sh` passed, the current repo gate now covers 79 passing backend unit and integration tests plus the built-frontend smoke path, the focused IFC slice `uv run pytest tests/integration/test_agent.py tests/unit/test_renderer.py tests/unit/test_validator_node.py -q` still passed, and `uv run python run_demo.py --mode full-workflow` still succeeds from `backend/study-guide-agent/`, writing `demo-output/study-guide-full-demo.pdf` with 18 preview sections, 0 failed sections, 0 best-effort sections, and non-blocking reading-level warnings only. The shipped backend now also strips HTML-like markup from model text before preview and PDF rendering, auto-repairs assessment-answer quote embedding when Gemini only fills `evidence_quote`, realigns answer-key assessment answers back to the upstream assessment-question text and exact passage-quote candidates on both first-pass generation and answer-key retries, grounds `assessment_questions` evidence requirements to exact assessment-passage quotes before downstream use, strips malformed inline clue-list annotations, multiline placeholder blocks, and code-like concatenation annotations before a second JSON parse attempt, and re-normalizes `answer_key` defensively inside validation and rendering. A fresh plain backend rerun of the Grade 12 nursing scenario now also succeeds after the parser hardening, so the earlier `assessment_passage` parse failure is no longer reproducible on that scenario with the current code. The live browser UI has now been rerun successfully for English, Science, Mathematics, and Nursing with 0 failed sections and 0 best-effort sections in each case, so the earlier `answer_key` and `assessment_passage` failure paths are no longer reproducible in that validation set with the current code. The signoff covers dependency ordering and one-pass retry in `backend/study-guide-agent/tests/integration/test_agent.py`, canonical preview/render ordering in `backend/study-guide-agent/app/nodes/renderer.py`, answer-key page breaks in `backend/study-guide-agent/app/templates/study_guide.html.j2`, market- and grade-aware prompting in `backend/study-guide-agent/app/prompts/system_prompt.py`, hard-validator aggregation in `backend/study-guide-agent/app/nodes/validator.py`, and frontend isolation through the thin backend proxy in `frontend/app/api/generate/route.ts`. The local runtime now auto-loads `backend/study-guide-agent/.env` for backend runs, so the demo and API-backed workflow no longer depend on separately exported shell variables just to find `GOOGLE_API_KEY`.

## Phase 13 — Deployment and parity

### Task 13.1 — Document the deployment topology and environment matrix

Status: `complete`
Notes: `DEPLOYMENT.md` now exists at the repo root and aligns the deployment plan across `IFC.md`, `ARCHITECTURE.md`, `TASKS.md`, and the repo README files around fast local dev, local parity, remote dev, and production.

### Task 13.2 — Containerize the backend for Cloud Run parity

Status: `complete`
Notes: The backend Dockerfile now installs the Linux runtime libraries WeasyPrint needs for PDF rendering, includes a build-time PDF smoke check, reads the runtime `PORT` environment variable instead of hardcoding the bind port, and successfully builds and boots locally as a containerized `app.fast_api_app:app` service on a non-default port; `DEPLOYMENT.md` now documents the local build/run commands and the Cloud Run deploy shape, and the repo done gate passed.

### Task 13.3 — Add a local parity orchestration path

Status: `complete`
Notes: `scripts/run-local-parity.sh` now provides the documented single-command local parity stack for the repo: it builds the backend Cloud Run-style container from `backend/study-guide-agent/Dockerfile`, runs it with `backend/study-guide-agent/.env` plus runtime `PORT` and local CORS settings, builds the frontend in production mode, and starts `next start` with `ADK_BACKEND_URL` pointed at the local backend container while cleaning both processes up on exit. Focused parity validation passed by serving the production frontend on `http://127.0.0.1:3000` and confirming `POST /api/generate` reached the backend through the proxy path, and `./scripts/validate-task.sh` also passed.

### Task 13.4 — Configure the backend deployment for Cloud Run

Status: `complete`
Notes: `app/fast_api_app.py` now reads deployment-facing runtime configuration from environment variables, including comma-separated `BACKEND_CORS_ALLOW_ORIGINS`, optional service URIs, telemetry toggles, and `PORT`; `scripts/deploy-backend-cloud-run.sh` now standardizes the dev/prod `gcloud run deploy` entrypoint with timeout, concurrency, memory, CPU, env-var, and secret flags; `DEPLOYMENT.md` and the backend README now document required environment variables, preview/production CORS guidance, and the standardized deploy path, and the repo done gate passed.

### Task 13.5 — Configure the frontend deployment for Vercel

Status: `complete`
Notes: `DEPLOYMENT.md` now documents the Vercel project-settings contract for `ADK_BACKEND_URL` across Development, Preview, and Production, `frontend/README.md` now documents the frontend deployment path and the requirement that `frontend/app/api/generate/route.ts` stay thin and environment-driven, and `frontend/.env.local.example` now explicitly marks the committed example as local-only while directing deployed values to Vercel project settings. Focused validation passed by running the same built frontend with different runtime `ADK_BACKEND_URL` configurations and observing different proxy behavior without code changes, and `./scripts/validate-task.sh` also passed.

### Task 13.6 — Run staged deployment checkpoints

Status: `not started`
Notes: No remote deployment checkpoints have been recorded yet after Phases 7, 10, or 12.

## Phase 14 — Prompt Lab MVP

### Task 14.1 — Extend the prompt-lab request contract and sample-input model

Status: `complete`
Notes: `backend/study-guide-agent/app/types.py` now defines `PromptLabGenerateRequest`, `PromptLabPromptOverrides`, the explicit `PromptLabSectionKey` allowlist, stable `PromptLabSampleCaseId` values, and `PromptLabSampleInput`, while `frontend/lib/types.ts` mirrors that contract for the frontend. Focused validation passed with `cd backend/study-guide-agent && uv run pytest tests/unit/test_prompt_lab_types.py -q` and `cd frontend && npm run typecheck`, and the repo done gate `./scripts/validate-task.sh` also passed.

### Task 14.2 — Add backend prompt override resolution for supported sections

Status: `complete`
Notes: `backend/study-guide-agent/app/prompts/runtime.py` now resolves prompt-lab requests into the base `GenerateRequest`, appends reviewer guidance to the system prompt, and injects supported section overrides into user prompts without modifying the default template files. The shared section generation path, blueprint node, answer-key node, and retry flow now all use that runtime layer, focused validation passed with `cd backend/study-guide-agent && uv run pytest tests/unit/test_prompt_lab_prompt_overrides.py`, and the repo done gate `./scripts/validate-task.sh` also passed.

### Task 14.3 — Add a prompt-lab backend endpoint and thin frontend proxy route

Status: `complete`
Notes: `backend/study-guide-agent/app/fast_api_app.py` now exposes a dedicated `/prompt-lab/generate` SSE endpoint that accepts `PromptLabGenerateRequest` and reuses the existing streaming workflow contract, while `frontend/app/api/prompt-lab/generate/route.ts` now forwards reviewer requests to that backend path through the same thin proxy pattern as the teacher flow. Focused validation passed with `cd backend/study-guide-agent && uv run pytest tests/integration/test_server_e2e.py -q` and `cd frontend && npm run typecheck`, and the repo done gate `./scripts/validate-task.sh` also passed.

### Task 14.4 — Add curated prompt-lab sample inputs

Status: `complete`
Notes: `backend/study-guide-agent/app/prompt_lab/sample_inputs/` now holds a curated prompt-lab sample set as checked-in `PromptLabSampleInput` JSON files, including English, Mathematics, Nursing/Health, Science, and Social Studies reviewer cases; `backend/study-guide-agent/app/prompt_lab/samples.py` now resolves those samples by stable id, and the backend plus frontend expose read-only prompt-lab sample routes so the later reviewer UI can preload a curated case or fetch the full catalog without mixing this data into teacher-facing defaults. Focused validation passed with `cd backend/study-guide-agent && uv run pytest tests/unit/test_prompt_lab_samples.py -q` and `cd frontend && npm run typecheck`, and the repo done gate `./scripts/validate-task.sh` also passed.

### Task 14.5 — Build the private prompt-lab page and reviewer editors

Status: `complete`
Notes: `frontend/app/prompt-lab/page.tsx` now provides a dedicated internal reviewer page that is separate from the teacher-facing flow, loads curated sample inputs via `/api/prompt-lab/samples`, lets reviewers edit the underlying request JSON, and includes plain-text prompt editors for system guidance plus the supported section override allowlist through `frontend/components/PromptLabSamplePicker.tsx` and `frontend/components/PromptLabEditor.tsx`. Focused validation passed with `cd frontend && npm run typecheck && npm run lint && npm run format:check`, and the repo done gate `./scripts/validate-task.sh` also passed.

### Task 14.6 — Reuse progress, preview, download, and validation results in prompt lab

Status: `complete`
Notes: The prompt-lab page now reuses the existing generation result workspace components (`ProgressTracker`, `WebPreview`, and `DownloadButton`) so reviewers get the same progress timeline, validation visibility, preview rendering, and PDF-download behavior as the teacher flow while running `PromptLabGenerateRequest` through the dedicated prompt-lab routes. Validation coverage for this reuse is included in the same frontend and done-gate checks used for Task 14.5.

### Task 14.7 — Add focused prompt-lab validation and documentation

Status: `complete`
Notes: Prompt-lab validation and docs are now implemented with focused coverage on both runtimes. Backend validation now includes override behavior and unsupported-key rejection coverage plus a curated-sample smoke path through `/prompt-lab/samples` -> `/prompt-lab/samples/{sample_id}` -> `/prompt-lab/generate` in `backend/study-guide-agent/tests/integration/test_server_e2e.py`; focused backend validation passed with `cd backend/study-guide-agent && uv run pytest tests/unit/test_prompt_lab_prompt_overrides.py tests/unit/test_prompt_lab_types.py tests/integration/test_server_e2e.py -k prompt_lab -q`. Frontend validation now includes `frontend/lib/promptLab.test.ts` covering prompt-lab request shaping and stream-state parsing from `frontend/lib/promptLab.ts`; focused frontend validation passed with `cd frontend && npm run typecheck && npm run lint && npm run test:prompt-lab`. Documentation is updated in `frontend/README.md` and `backend/study-guide-agent/README.md`, and the repo done gate `./scripts/validate-task.sh` also passed.

## Guidance for future chats

- Read this file and `TASKS.md` together before starting new implementation work.
- Update the status of the exact matching task after implementation and a focused validation step.
- Build on `complete` tasks freely.
- Treat `partial` tasks as existing scaffolds that may need refactoring before extension.
