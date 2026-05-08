# Codebase State

Last updated: 2026-05-08

This document is the live plain-language summary of the shipped codebase.
It is intended to answer, in words, what currently exists in the repository without requiring a reader to inspect source files directly.

## Executive Summary

- The repository now includes a working Copilot automation loop with workspace-local skills, a repo-level validation script, and a live shipped-state document.
- The backend now includes implemented Wave 1, Wave 2, Wave 3, and answer-key generation slices beyond blueprint generation.
- The ADK FastAPI loader now has a compatibility adapter so the server integration path can locate `study_guide_agent.root_agent` correctly.

## Repository Shape

- The repository is split into two runtimes: `frontend/` for the Next.js app and `backend/study-guide-agent/` for the ADK backend.
- The scaffolded backend under `backend/study-guide-agent/` is the only canonical backend implementation path.
- Root planning and control documents are `IFC.md`, `ARCHITECTURE.md`, `TASKS.md`, and `TASK_STATUS.md`.

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
- The backend uses the scaffolded ADK project structure created by `agents-cli`.
- Core typed contracts are implemented in `backend/study-guide-agent/app/types.py` and mirrored in `frontend/lib/types.ts`.
- The repo includes a compatibility shim in `backend/study-guide-agent/app/app_utils/adk_compat.py` to smooth over current ADK beta import-surface issues before ADK imports are loaded.
- The blueprint generation path is the most implemented backend slice at the moment.
- The repo now includes `backend/study-guide-agent/study_guide_agent/agent.py` as an ADK loader adapter that re-exports the real agent from `app.agent` for CLI and FastAPI loading.

## Shipped Frontend

- The frontend runtime exists as a Next.js 14 scaffold with shared type definitions.
- Product-facing frontend experience work is still limited compared with the backend blueprint slice.

## Automation Workflow

- Workspace-local Copilot workflow skills exist under `.github/skills/`.
- The routing entrypoint is `repo-automation`.
- The main implementation loop is `task-implement` -> `task-done` -> `docs-drift`.
- `task-done` is intended to require the repo-level validation script and create a small iterative commit once the done gate passes.
- The default iterative commit message format is `task(<task-id>): <imperative summary>`, or `task: <imperative summary>` when no task id applies.
- `docs-drift` is responsible for keeping this document current.

## Validation And Quality Gates

- The repository now has a repo-level validation script at `scripts/validate-task.sh`.
- That script is intended to run backend lint, backend unit tests, backend integration tests, and frontend lint when those checks exist.
- Backend lint passes under the repo-level validation script.
- The backend `test_chat_stream` integration failure caused by ADK loader discovery has been resolved by the new loader adapter package.
- Python analysis for backend files is now pinned through `pyrightconfig.json` so the backend venv is used for import resolution in editor diagnostics.
- The full repo-level validation script now passes end to end, including backend lint, backend tests, and frontend lint.
- The repo-level validation script now also runs backend Pyright against the shared repo `pyrightconfig.json`, so editor-visible backend type errors can fail the done gate before a task is marked complete.

## Current Product Gaps

- Wave 1, Wave 2, Wave 3, and answer-key generation are implemented, but validators and renderer files still exist only as placeholders.
- End-to-end workflow orchestration is still partial rather than complete.
- Phase 4 onward remains mostly scaffolded or placeholder-only, including section generation nodes, validators, renderer implementation, and most frontend product experience work.
