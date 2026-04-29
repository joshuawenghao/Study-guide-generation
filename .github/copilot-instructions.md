# Copilot Instructions — Study Guide Generation

## Project overview

This project is a web application that generates complete, curriculum-aligned study guides for K–12 teachers. A teacher fills in a single form (lesson metadata, curriculum details, and instructional design inputs) and receives a fully structured, print-ready PDF plus a web preview — without any additional editing steps.

The backend is an **ADK 2.0 dynamic workflow** (Python) that calls **Gemini 2.0 Flash** to generate each of the 17 fixed sections in dependency order, validates every output against hard and soft constraints, automatically retries sections that fail, and then renders the final PDF with WeasyPrint. The frontend is **Next.js 14** with Tailwind CSS.

Full architectural detail is in `ARCHITECTURE.md`. Project rationale and acceptance criteria are in `IFC.md`.

---

## Hard validation rules

Hard validators **block document assembly**. A section that fails a hard validator is retried once automatically during the validation pass. If the second attempt also fails, the document is assembled with a visible warning badge on the affected section (`best_effort=True`).

There are five hard validators. Every implementation must respect these rules exactly.

### 1. `vocab_presence`

**Rule:** Every vocabulary word listed in the blueprint must appear — case-insensitively — somewhere in the combined text of all body sections.

- **What counts as a body section:** every generated section *except* the vocabulary-definition section itself and the answer key. In practice this means: intro, learning targets, warm-up, core explainer, all sub-concept blocks, strategy list, deep dive, model passage, check-in, key points, assessment passage, assessment questions, step-up, and self-assessment.
- **Match type:** substring, case-insensitive. The word `"photosynthesis"` matches `"Photosynthesis"`, `"PHOTOSYNTHESIS"`, etc.
- **Failure unit:** one failure message per missing vocabulary word, naming the word.
- **Applies to:** all body sections collectively. This is a cross-section validator and cannot be run per-section.
- **Implemented in:** `backend/validators/hard/vocab_presence.py`

### 2. `self_assess_targets`

**Rule:** Each skill row in the self-assessment section must match exactly one learning target objective from the blueprint — verbatim (exact string equality, case-sensitive).

- **Failure unit:** one failure message per skill row that does not match any learning target objective verbatim.
- **Applies to:** the `self_assessment` section output only.
- **Implemented in:** `backend/validators/hard/self_assess_targets.py`

### 3. `answer_key_quotes`

**Rule:** Each possible answer in the answer key must contain a verbatim phrase — a contiguous substring — from the assessment passage text. Paraphrasing is not permitted.

- **Match type:** the answer text must contain a substring that also appears in the assessment passage text. Both sides are tokenized by stripping punctuation from word boundaries before comparison. A phrase of at least three consecutive word tokens is required; shorter fragments do not qualify.
- **Failure unit:** one failure message per possible answer that contains no verbatim phrase from the assessment passage.
- **Applies to:** the `answer_key` section output, cross-referencing the `assessment_passage` section output.
- **Implemented in:** `backend/validators/hard/answer_key_quotes.py`

### 4. `passage_domain_diff`

**Rule:** The topic domain assigned to the assessment passage must be **different** from the topic domain assigned to the model passage. Identical domains indicate a risk of answer leakage from the model passage into the assessment.

- **Comparison:** exact string equality on the domain values from `blueprint.topic_domains`. If `blueprint.topic_domains.assessment_passage == blueprint.topic_domains.model_passage`, the validator fails.
- **Failure unit:** a single failure message naming both domains.
- **Applies to:** the `assessment_passage` section node (triggered when the blueprint is checked before generation and again during the validation pass).
- **Implemented in:** `backend/validators/hard/passage_domain_diff.py`

### 5. `json_schema`

**Rule:** Every section output must parse correctly against its expected JSON schema (defined as a Pydantic model in `backend/types.py`). Structurally invalid or missing-field responses from Gemini must be caught immediately after each section node runs, before the validation pass.

- **When it runs:** immediately after each section node call, not deferred to the validation pass.
- **Failure unit:** a single failure message per section, including the Pydantic validation error detail.
- **Applies to:** all section nodes.
- **Retry behaviour:** a schema failure on the first attempt triggers a retry. If the retry also fails, the section is marked `best_effort`.
- **Implemented in:** each section node (inline parse + validation) using Pydantic `.model_validate()`.

---

## Soft validation rules

Soft validators produce **warnings only**. They do not block document assembly and do not trigger retries. Warnings are surfaced as amber inline callouts in the web preview.

| Validator | Rule |
|---|---|
| `answer_leakage` | Body sections must not contain verbatim phrases that appear in the answer key possible answers. |
| `reading_level` | Each section's Flesch-Kincaid grade score must fall within ±1.0 of the target grade band. |

Soft validators are implemented in `backend/validators/soft/`.

---

## Key constraints to enforce in all generated code

- **No answer leakage:** never pass answer key content to section generation nodes that run before the answer key. The answer key node is always last in the execution order.
- **Dependency ordering:** check-in depends on model passage; assessment questions depend on assessment passage; step-up depends on assessment questions; answer key depends on check-in and assessment questions. These dependencies are wired in `agent.py` via `ctx.run_node()` argument threading — do not bypass them.
- **Verbatim matching:** for `self_assess_targets` and `answer_key_quotes`, the matching rule is verbatim (exact string). Do not use fuzzy matching, stemming, or semantic similarity for these validators.
- **Single retry pass:** the orchestrator retries each failed section at most once. After one retry the section is included as `best_effort` regardless of the second result.
- **Validator must not raise:** `validator_node` captures all failures in a `ValidationResult` return value. It must not raise exceptions to the orchestrator.
