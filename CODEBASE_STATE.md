# Codebase State

Last updated: 2026-05-14

This document is the live plain-language summary of the shipped codebase.
It is intended to answer, in words, what currently exists in the repository without requiring a reader to inspect source files directly.

## Executive Summary

- The repository now includes a working Copilot automation loop with workspace-local skills, a repo-level validation script, and a live shipped-state document.
- The backend now includes implemented Wave 1, Wave 2, Wave 3, and answer-key generation slices beyond blueprint generation.
- The backend now exports the real ADK workflow entrypoint from `app/agent.py`, wiring blueprint generation, parallel section waves, validator retry, and rendering into one `Workflow` root agent.
- The backend container now honors the runtime `PORT` environment variable and has been validated to boot the FastAPI app from the same image shape intended for Cloud Run.
- The backend deployment path now has a repo-standardized Cloud Run entrypoint and environment-driven CORS/runtime configuration, so dev and production services can be configured without code edits.
- The validation layer now has a working validator node that aggregates five hard validators and two soft validators into a single `ValidationResult` for the orchestrator retry loop and preview warnings.
- The ADK FastAPI loader now has a compatibility adapter so the server integration path can locate `study_guide_agent.root_agent` correctly.
- The repo documentation now includes an explicit deployment plan and task phase covering Vercel, Cloud Run, and a production-like local parity mode.

## Repository Shape

- The repository is split into two runtimes: `frontend/` for the Next.js app and `backend/study-guide-agent/` for the ADK backend.
- The scaffolded backend under `backend/study-guide-agent/` is the only canonical backend implementation path.
- Root planning and control documents are `IFC.md`, `ARCHITECTURE.md`, `TASKS.md`, and `TASK_STATUS.md`.
- `DEPLOYMENT.md` now serves as the deployment-specific reference for environment topology, parity goals, and staged deployment checkpoints.

## Shipped Backend

- Phase 3 of the planned backend work is complete: the system prompt builder, blueprint prompt template, blueprint node, and focused blueprint unit test exist.
- Task 4.1 is now implemented: the Wave 1 prompt templates for intro, learning targets, warm-up, vocabulary, key points, and self-assessment now build blueprint-driven prompts with explicit inline JSON schemas.
- The backend now includes a focused unit test for those Wave 1 prompt templates using the preserved Grade 6 English fixture shape.
- Task 4.2 is now implemented: the Wave 1 section nodes for intro, learning targets, warm-up, vocabulary, key points, and self-assessment now build request-aware system prompts, call Gemini through the shared section wrapper, parse JSON objects, and expose ADK node exports with explicit `request` and `blueprint` inputs.
- The backend now includes a focused unit test for the Wave 1 section nodes, covering both successful structured JSON generation and malformed JSON failure handling.
- Task 4.3 is now implemented: the Wave 2 prompt templates and section nodes for core explainer, subconcept, strategy list, deep dive, model passage, and assessment passage now generate blueprint-aware JSON prompts and request-aware node wrappers.
- The shared section helper now supports section-specific `spec` inputs so `subconcept` generation can run once per sub-competency without reading from session state.
- The backend now includes a focused Wave 2 unit test covering sub-competency-aware prompt generation, passage-domain-aware generation, and malformed JSON failure handling.
- Task 4.4 is now implemented: the Wave 3 prompt templates and section nodes for check-in, assessment questions, and step-up now consume upstream section payloads directly through explicit node arguments rather than shared session state.
- The backend now includes a focused Wave 3 unit test covering dependency-aware prompt generation for passage-based questions and malformed JSON failure handling.
- Task 4.5 is now implemented: the answer-key prompt template and node now consume check-in, assessment passage, and assessment question payloads directly, use `TEMP_ANSWER_KEY`, and require quoted passage evidence in assessment answers.
- The backend now includes a focused answer-key unit test covering both structured output shape and malformed JSON failure handling.
- Task 4.6 is now implemented: `tests/unit/test_section_generation.py` provides a dedicated representative section-generation module that covers a few Wave 1 node calls, a dependency-aware Wave 3 node, and answer-key output shape without testing the whole workflow.
- Task 5.1 is now implemented: `app/validators/hard/json_schema.py` validates generated section payloads against backend Pydantic section models and reports failures through `ValidationResult` instead of raising hard-validation exceptions.
- The backend now includes focused unit coverage for that validator in `tests/unit/test_json_schema_validator.py`, covering both a passing payload and a schema-failure payload.
- Task 5.2 is now implemented: `app/validators/hard/vocab_presence.py` validates that every blueprint vocabulary word appears case-insensitively across combined body-section text, while excluding the vocabulary section and answer key from the search corpus.
- The backend now includes focused unit coverage for that validator in `tests/unit/test_vocab_presence_validator.py`, covering both a passing body-section match and a failing case where excluded sections cannot satisfy the requirement.
- Task 5.3 is now implemented: `app/validators/hard/self_assess_targets.py` validates that each self-assessment skill matches a blueprint learning-target objective verbatim and fails only the `self_assessment` slice when rows paraphrase or diverge.
- The backend now includes focused unit coverage for that validator in `tests/unit/test_self_assess_targets_validator.py`, covering both exact verbatim matches and a failing non-verbatim skill row.
- Task 5.4 is now implemented: `app/validators/hard/answer_key_quotes.py` validates that each assessment answer in the answer key contains a quoted phrase and that at least one quoted phrase appears verbatim in the assessment passage body.
- The backend now includes focused unit coverage for that validator in `tests/unit/test_answer_key_quotes_validator.py`, covering a passing verbatim quote plus failures for missing quotes and non-verbatim quoted phrases.
- Task 5.5 is now implemented: `app/validators/hard/passage_domain_diff.py` validates that the blueprint model-passage and assessment-passage topic domains are both present and differ case-insensitively, failing the `assessment_passage` slice when they collapse to the same domain.
- The backend now includes focused unit coverage for that validator in `tests/unit/test_passage_domain_diff_validator.py`, covering distinct domains, case-insensitive equality failure, and blank-domain failure.
- Task 5.6 is now implemented: `app/validators/soft/answer_leakage.py` extracts quoted evidence phrases from assessment answer-key `possible_answer` fields and warns when those phrases reappear in other body sections, while intentionally excluding the assessment passage and answer key from the search surface.
- The backend now includes focused unit coverage for that validator in `tests/unit/test_answer_leakage_validator.py`, covering both a clean case where the quote remains only in the assessment passage and a warning case where a body section repeats the quoted phrase.
- Task 5.7 is now implemented: `app/validators/soft/reading_level.py` flattens section text, computes Flesch-Kincaid grade scores through `textstat`, and emits warnings when a section falls outside a ±1.0 band around the target grade level.
- The backend now includes focused unit coverage for that validator in `tests/unit/test_reading_level_validator.py`, and `backend/study-guide-agent/pyproject.toml` plus `backend/study-guide-agent/uv.lock` now include the `textstat` dependency needed for runtime scoring.
- Task 5.8 is now implemented: `app/nodes/validator.py` runs json-schema checks across all generated section payloads, aggregates the implemented hard and soft validator outputs into one `ValidationResult`, and skips downstream model-based validators when schema validation already failed for the same slice.
- The backend now includes focused unit coverage for that node in `tests/unit/test_validator_node.py`, covering both repeated section schema iteration and aggregated failure-plus-warning behavior.
- Task 5.9 is now effectively complete: the validator layer now has isolated pytest coverage across the hard validators, soft validators, and validator node, including the planned pass/fail coverage for `vocab_presence` and `answer_key_quotes`, a failing case for `self_assess_targets` and `passage_domain_diff`, and a warning-only case for `answer_leakage`.
- The broader validator test surface now spans `tests/unit/test_json_schema_validator.py`, `tests/unit/test_vocab_presence_validator.py`, `tests/unit/test_self_assess_targets_validator.py`, `tests/unit/test_answer_key_quotes_validator.py`, `tests/unit/test_passage_domain_diff_validator.py`, `tests/unit/test_answer_leakage_validator.py`, `tests/unit/test_reading_level_validator.py`, and `tests/unit/test_validator_node.py`.
- Task 6.1 is now implemented: `backend/study-guide-agent/app/templates/study_guide.html.j2` defines the canonical PDF layout in Jinja2 for WeasyPrint, including the fixed study-guide section order, vocabulary and self-assessment tables, validation warning callouts, and explicit page breaks for the assessment passage and answer key.
- Task 6.2 is now implemented: `backend/study-guide-agent/app/nodes/renderer.py` renders the study-guide template with explicit `blueprint`, `sections`, and `validation` inputs, converts the HTML to PDF through WeasyPrint, base64-encodes the PDF bytes, and returns a `GenerateResponse` that includes a canonical-order `WebPreviewPayload` for the frontend.
- Task 6.3 is now implemented: `backend/study-guide-agent/tests/unit/test_renderer.py` exercises the renderer directly with a minimal valid blueprint and section payloads, checks that the emitted PDF artifact decodes to bytes beginning with a PDF header, and verifies that preview sections are returned in canonical order.
- Task 7.1 is now implemented: `backend/study-guide-agent/app/agent.py` exports a `Workflow` root agent whose orchestrator node runs blueprint generation first, fans out Wave 1 and Wave 2 with `asyncio.gather()`, runs Wave 3 with explicit upstream section inputs, generates the answer key last, validates all sections, retries failed sections once with failure-specific retry guidance at `TEMP_RETRY`, and renders the final `GenerateResponse`.
- Task 7.2 is now implemented: `backend/study-guide-agent/tests/integration/test_agent.py` adds a focused backend-only integration test that executes the real orchestrator function through a fake ADK context, stubs the generation and rendering edges, and verifies dependency ordering plus the single retry pass from validation failure to successful render.
- Because ADK `ctx.run_node()` accepts a single node input rather than unpacking multiple function parameters, `app/agent.py` now owns workflow-local adapter nodes that translate composite workflow inputs into the existing section, validator, and renderer generator functions without introducing session-state dictionaries.
- The backend project now declares `jinja2` and `weasyprint` as direct runtime dependencies in `backend/study-guide-agent/pyproject.toml` so the renderer path is available in the managed environment and the repo validation gate.
- Task 13.2 is now implemented: the backend Dockerfile installs the Linux `glib` and `pango` runtime libraries WeasyPrint depends on, runs a build-time PDF smoke check, reads `PORT` from the runtime environment for Cloud Run parity, and has been validated by building locally and serving `app.fast_api_app:app` from the same image on a non-default port.
- Task 13.4 is now implemented: `backend/study-guide-agent/app/fast_api_app.py` reads `BACKEND_CORS_ALLOW_ORIGINS`, optional service URIs, telemetry toggles, and `PORT` from the runtime environment, and `scripts/deploy-backend-cloud-run.sh` standardizes the `gcloud run deploy` entrypoint for `dev` and `prod` with the repo's current timeout, concurrency, resource, env-var, and secret assumptions.
- Task 13.3 is now partially implemented: `backend/study-guide-agent/run_demo.py` provides a repeatable local backend demo flow for both renderer-only and full-workflow PDF generation, writes output PDFs under `backend/study-guide-agent/demo-output/`, supports teacher-style partial request overrides, and can open the generated file locally for inspection, but the full production-frontend-plus-containerized-backend parity stack is still not in place.
- The local demo runner now also prints the full `validation_warnings` list in its full-workflow JSON summary, so remaining soft-validator output can be inspected directly from the terminal during demo and parity checks.
- The local reading-level path now auto-detects a project-local `backend/study-guide-agent/.nltk_data/cmudict` install when it exists, uses the primary `textstat` path in that case, and otherwise falls back to a local Pyphen-based estimate instead of surfacing a dependency warning or noisy NLTK download attempt.
- The renderer template now tolerates best-effort answer-key payload drift during local full-workflow demos, so missing `evidence_quote` fields or string-shaped `step_up_answer` values no longer abort PDF generation.
- The reading-level validator now focuses on longer prose-heavy sections rather than short structured scaffolds, and the main prose prompts now include stricter plain-language guidance. Passage prompts also adapt paragraph-count guidance by grade level and `length_preset`, reducing Grade 6 warning noise without hardcoding the same short-passage requirement for all grades.
- The shared section parser now hardens full-workflow generation against LLM JSON escape issues by repairing lone backslashes before `json.loads(...)` and normalizing accidental control-escape sequences like `\frac`, so math-style outputs no longer intermittently derail local PDF rendering.
- The lower-grade readability path is now stricter in prompts but slightly more realistic in scoring: the system prompt adds plain-text math-notation guidance for mathematics requests, the intro and deep-dive prompts add stronger elementary-grade brevity guidance, and the reading-level validator uses a modestly wider tolerance band for lower grades so local demos surface fewer borderline warnings without hiding clearly off-target prose.
- The backend uses the scaffolded ADK project structure created by `agents-cli`.
- Core typed contracts are implemented in `backend/study-guide-agent/app/types.py` and mirrored in `frontend/lib/types.ts`.
- `backend/study-guide-agent/app/types.py` now also contains the backend-only section payload models that the validation layer uses as its schema source of truth.
- The repo includes a compatibility shim in `backend/study-guide-agent/app/app_utils/adk_compat.py` to smooth over current ADK beta import-surface issues before ADK imports are loaded.
- The repo now includes focused backend integration coverage for both the exported workflow surface and the orchestrator behavior: one integration test validates the `Workflow` export and retry-capable orchestration path, and another validates FastAPI boot plus session creation.
- The repo now includes `backend/study-guide-agent/study_guide_agent/agent.py` as an ADK loader adapter that re-exports the real agent from `app.agent` for CLI and FastAPI loading.
- `DEPLOYMENT.md` now includes concrete backend container commands for local build, local run, alternate-port parity runs, and the intended Cloud Run deploy shape.
- `DEPLOYMENT.md` and `backend/study-guide-agent/README.md` now also document the standardized backend Cloud Run deploy command, required env vars and secret sources, CORS origin guidance for preview versus production, and the current timeout/concurrency assumptions for long-running generation requests.

## Shipped Frontend

- The frontend runtime now has a teacher-facing shell: `frontend/app/layout.tsx` sets study-guide product metadata and a persistent header, while `frontend/app/globals.css` defines the shared canvas, typography, and surface styling for the app.
- `frontend/app/page.tsx` no longer uses the default Create Next App scaffold and is now aligned to that shell with a minimal study-guide placeholder screen.
- The frontend now also includes the initial component structure under `frontend/components/`, with stub exports for `InputForm`, `ProgressTracker`, `WebPreview`, `DownloadButton`, and `PreviewSection`, while shared type definitions remain in place.
- Product-facing frontend experience work is still limited compared with the backend blueprint slice; the teacher input form, streaming progress flow, and preview experience are still ahead.

## Automation Workflow

- Workspace-local Copilot workflow skills exist under `.github/skills/`.
- The routing entrypoint is `repo-automation`.
- The main implementation loop is `task-implement` -> `task-done` -> `docs-drift`.
- `task-done` is intended to require the repo-level validation script and create a small iterative commit once the done gate passes.
- The default iterative commit message format is `task(<task-id>): <imperative summary>`, or `task: <imperative summary>` when no task id applies.
- `docs-drift` is responsible for keeping this document current.
- Deployment planning is now tracked explicitly in `TASKS.md` and `TASK_STATUS.md` rather than being implied by backend scaffold defaults.

## Validation And Quality Gates

- The repository now has a repo-level validation script at `scripts/validate-task.sh`.
- That script is intended to run backend lint, backend unit tests, backend integration tests, and frontend lint when those checks exist.
- Backend lint passes under the repo-level validation script.
- The backend integration smoke surface now validates that the exported root agent is a constructible `Workflow` and that the FastAPI server boots and supports session creation without relying on the removed scaffold chat-bootstrap behavior.
- Python analysis for backend files is now pinned through `pyrightconfig.json` so the backend venv is used for import resolution in editor diagnostics.
- The full repo-level validation script now passes end to end, including backend lint, backend tests, and frontend lint.
- The repo-level validation script now also runs backend Pyright against the shared repo `pyrightconfig.json`, so editor-visible backend type errors can fail the done gate before a task is marked complete.

## Current Product Gaps

- Wave 1, Wave 2, Wave 3, and answer-key generation are implemented; the validator layer now includes its aggregator node, five hard validators, two soft validators, broad isolated test coverage, and the complete Phase 6 renderer slice including template, node, and focused renderer tests.
- Workflow orchestration and focused backend integration coverage are now implemented.
- The remaining major gaps are most frontend product experience work plus the unfinished Phase 13 parity and remote deployment tasks.
- Deployment is now specified, and the backend image plus Cloud Run backend configuration path are in place, but the parity stack, Vercel setup, and staged remote deployment checkpoints are still not implemented or validated end to end.
