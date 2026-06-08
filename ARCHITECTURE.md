# Architecture

## Study Guide Generation Web App

> This document should be read alongside `IFC.md`. Every architectural decision here is traceable to a criterion in that document.

---

## Table of contents

1. [System overview](#1-system-overview)
2. [Tech stack decisions](#2-tech-stack-decisions)
3. [Repository structure](#3-repository-structure)
4. [ADK agent graph](#4-adk-agent-graph)
5. [Graph nodes reference](#5-graph-nodes-reference)
6. [Data contracts](#6-data-contracts)
7. [Validation layer](#7-validation-layer)
8. [Rendering pipeline](#8-rendering-pipeline)
9. [Frontend architecture](#9-frontend-architecture)
10. [Deployment architecture](#10-deployment-architecture)
11. [Key design decisions and alternatives considered](#11-key-design-decisions-and-alternatives-considered)

---

## 1. System overview

The system is a web application with two logical layers: a **Next.js frontend** that collects teacher inputs and displays results, and an **ADK agent graph** that drives all generation, validation, and retry logic on the backend.

The frontend and backend communicate over a single HTTP endpoint for the teacher-facing flow. The frontend sends a structured lesson request and streams progress events back; the backend runs the full dynamic workflow and returns a completed PDF and a structured web preview payload.

An internal prompt-lab surface may reuse the same workflow with temporary prompt overrides, but it must remain a reviewer-only experience and must not replace or destabilize the default teacher-facing request path.

```mermaid
flowchart LR
    subgraph Frontend ["Next.js Frontend (localhost:3000 / Firebase App Hosting)"]
        Form["Input Form\n(lesson metadata,\ncurriculum, etc.)"]
      PromptLab["Prompt Lab\n(private reviewer page)"]
        Tracker["Progress Tracker"]
        Preview["Web Preview"]
        Download["PDF Download"]
    end

    subgraph Backend ["ADK Backend (localhost:8000 / Cloud Run)"]
        Workflow["Dynamic Workflow\n(blueprint → sections →\nvalidate → retry? → render)"]
        Gemini["Gemini 2.0 Flash\n(all LLM calls)"]
        Workflow --> Gemini
    end

    Form -- "POST /generate\n(GenerateRequest JSON)" --> Workflow
    PromptLab -- "POST /prompt-lab/generate\n(PromptLabGenerateRequest JSON)" --> Workflow
    Workflow -- "SSE stream\n(ProgressEvents)" --> Tracker
    Workflow -- "GenerateResponse\n(pdf_base64 + preview JSON)" --> Preview
    Preview --> Download
```

---

## 2. Tech stack decisions

| Layer                      | Choice                                                           | Reason                                                                                                                                                                                     |
| -------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Frontend framework         | Next.js 14 (App Router)                                          | Single repo for UI and API proxy; SSE streaming support built in                                                                                                                           |
| Styling                    | Tailwind CSS                                                     | Utility-first, no design system overhead for a prototype                                                                                                                                   |
| Agent framework            | Google ADK 2.0 Python (dynamic workflows)                        | `@node` + `ctx.run_node()` with automatic checkpointing; conditional retry via `while` loop; native Gemini integration                                                                     |
| LLM                        | Gemini 2.0 Flash                                                 | Best cost/latency ratio for 17 sequential/parallel calls; ADK has first-class Gemini support                                                                                               |
| PDF rendering              | WeasyPrint (Python)                                              | HTML/CSS → PDF with full layout control; runs server-side in the ADK process                                                                                                               |
| Web preview                | Structured JSON → React components                               | Preview is assembled from the same section JSON that feeds the PDF renderer                                                                                                                |
| Deployment (Fast local)    | Next.js dev server + scaffolded FastAPI backend                  | Fastest iteration loop for feature work; no container build step                                                                                                                           |
| Deployment (Local parity)  | Production-mode Next.js frontend + backend container locally     | Mirrors the remote two-runtime topology and routing contract closely enough for production bug reproduction                                                                                |
| Deployment (Managed cloud) | Firebase App Hosting (frontend) + Google Cloud Run (ADK backend) | Best fit for the split stack under the current platform constraints: App Hosting preserves the Next.js server runtime and thin proxy route, while Cloud Run fits Python ADK and WeasyPrint |

### Why ADK dynamic workflows over graph-based workflows or a plain orchestrator

ADK 2.0 offers two workflow styles. **Graph-based workflows** define execution as a static `edges` array with `JoinNode` for fan-out and `Event(route=...)` for branching. **Dynamic workflows** use the `@node` decorator and `ctx.run_node()` called from plain Python code, with automatic checkpointing of each node execution.

Dynamic workflows are chosen for this project for three specific reasons:

1. **Automatic checkpointing for retry.** When the workflow resumes after a validation failure, ADK's deterministic execution IDs mean nodes that already completed are automatically skipped. Retrying only the failed sections requires a `while` loop calling `ctx.run_node()` — not 16 explicit retry edges in a graph definition.

2. **Readable parallel execution.** `asyncio.gather()` inside a `@node` function expresses wave-based parallel execution in standard Python. The graph-based equivalent requires a `JoinNode` per wave and careful `edges` array construction that becomes unwieldy at 16 sections.

3. **Future agent extensibility.** Adding a reading-level validator or curriculum alignment step requires adding one `ctx.run_node()` call in the workflow function, not restructuring an `edges` array and registering new routes.

---

## 3. Repository structure

```
/
├── frontend/                        # Next.js 14 application
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                 # Input form + generation UI
│   │   ├── prompt-lab/
│   │   │   └── page.tsx             # Private reviewer-only prompt tuning page
│   │   └── api/
│   │       └── generate/
│   │           └── route.ts         # Proxy to ADK backend + SSE stream
│   │       └── prompt-lab/
│   │           └── generate/
│   │               └── route.ts     # Proxy for prompt-lab runs with temporary prompt overrides
│   ├── components/
│   │   ├── InputForm.tsx
│   │   ├── PromptLabEditor.tsx
│   │   ├── PromptLabSamplePicker.tsx
│   │   ├── ProgressTracker.tsx
│   │   ├── WebPreview.tsx           # Renders section JSON as styled HTML
│   │   └── DownloadButton.tsx
│   ├── lib/
│   │   └── types.ts                 # Shared TypeScript types (mirrored from backend)
│   └── package.json
│
└── backend/
  └── study-guide-agent/           # Canonical agents-cli backend project
    ├── app/
    │   ├── agent.py             # root_agent + App entrypoint
    │   ├── fast_api_app.py      # FastAPI server for the frontend proxy
    │   ├── types.py             # Pydantic models for all data contracts
    │   ├── nodes/
    │   │   ├── base.py          # Shared Gemini client + call wrapper
    │   │   ├── blueprint.py     # Node: generate blueprint JSON
    │   │   ├── validator.py     # Node: runs all hard + soft validators
    │   │   ├── renderer.py      # Node: assembles validated JSON → PDF + preview JSON
    │   │   └── sections/
    │   │       ├── intro.py
    │   │       ├── learning_targets.py
    │   │       ├── warmup.py
    │   │       ├── vocabulary.py
    │   │       ├── core_explainer.py
    │   │       ├── subconcept.py
    │   │       ├── strategy_list.py
    │   │       ├── deep_dive.py
    │   │       ├── model_passage.py
    │   │       ├── check_in.py
    │   │       ├── key_points.py
    │   │       ├── assessment_passage.py
    │   │       ├── assessment_questions.py
    │   │       ├── step_up.py
    │   │       ├── self_assessment.py
    │   │       └── answer_key.py
    │   ├── prompts/
    │   │   ├── system_prompt.py
    │   │   └── templates/
    │   ├── validators/
    │   │   ├── hard/
    │   │   └── soft/
    │   └── templates/
    │       └── study_guide.html.j2
    ├── tests/
    │   ├── eval/evalsets/       # agents-cli evalsets
    │   ├── fixtures/legacy_evals/ # preserved legacy acceptance fixtures
    │   ├── integration/
    │   └── unit/
    ├── .env.example
    ├── pyproject.toml
    └── uv.lock
```

**Key structural rule:** The canonical backend project root is `backend/study-guide-agent/`. All backend code now lives inside its `app/` package, and tests, evalsets, and preserved legacy fixtures live under `backend/study-guide-agent/tests/`.

---

## 4. ADK dynamic workflow

The backend is implemented as an ADK 2.0 **dynamic workflow** using the `@node` decorator and `ctx.run_node()`. This is distinct from ADK's graph-based workflow (`Workflow` + `edges` array) — dynamic workflows express execution order as plain Python code with automatic checkpointing of every node execution.

### Why dynamic workflow over graph-based workflow

ADK 2.0 offers both styles. Graph-based workflows suit simple linear or branching pipelines. Dynamic workflows are chosen here because:

- Retry logic for failed sections is a `while` loop — not 16 explicit retry edges in an `edges` array
- Wave parallelism is `asyncio.gather()` — not a `JoinNode` per wave
- Checkpointing is automatic — nodes that completed are skipped on resume without any manual state bookkeeping

### Workflow structure

```mermaid
flowchart TD
    START(["START\n(GenerateRequest written\nto context)"])
    BP["blueprint_node\n(generates shared Blueprint JSON)"]

    subgraph Wave1 ["Wave 1 — asyncio.gather() — blueprint only"]
        W1A["intro_node"]
        W1B["learning_targets_node"]
        W1C["warmup_node"]
        W1D["vocabulary_node"]
        W1E["key_points_node"]
        W1F["self_assessment_node"]
    end

    subgraph Wave2 ["Wave 2 — asyncio.gather() — blueprint only"]
        W2A["core_explainer_node"]
        W2B["subconcept_node ×N\n(one per sub-competency)"]
        W2C["strategy_list_node"]
        W2D["deep_dive_node"]
        W2E["model_passage_node"]
        W2F["assessment_passage_node"]
    end

    subgraph Wave3 ["Wave 3 — depends on Wave 2 outputs"]
        W3A["check_in_node\n(depends on: model_passage)"]
        W3B["assessment_questions_node\n(depends on: assessment_passage)"]
        W3C["step_up_node\n(depends on: assessment_questions)"]
    end

    AK["answer_key_node\n(always last — depends on\ncheck_in + assessment_questions)"]

    VAL["validator_node\n(runs all hard + soft validators)"]

    RETRY{"validation\npassed?"}

    subgraph RetryLoop ["Retry loop — while failed_sections:"]
      RL["ctx.run_node() for each\nfailed section only\n(failure-specific retry prompt\n+ TEMP_RETRY)"]
        RVAL["validator_node\n(second pass)"]
    end

    RENDER["renderer_node\n(Jinja2 → WeasyPrint → PDF\n+ WebPreviewPayload JSON)"]
    END(["END\n(GenerateResponse returned)"])

    START --> BP
    BP --> Wave1
    Wave1 --> Wave2
    Wave2 --> Wave3
    Wave3 --> AK
    AK --> VAL
    VAL --> RETRY
    RETRY -- "yes" --> RENDER
    RETRY -- "no" --> RetryLoop
    RetryLoop --> RENDER
    RENDER --> END
```

### agent.py skeleton

The entry point uses ADK's `Workflow` with a single dynamic workflow node as the orchestrator:

```python
from google.adk import Workflow
from google.adk import node, Context
import asyncio

@node(rerun_on_resume=True)
async def study_guide_workflow(ctx: Context, request: GenerateRequest):
    # Stage 1 — blueprint
    blueprint = await ctx.run_node(blueprint_node, request)

    # Stage 2 — Wave 1 (parallel, blueprint only)
    wave1_results = await asyncio.gather(
        ctx.run_node(intro_node, blueprint),
        ctx.run_node(learning_targets_node, blueprint),
        ctx.run_node(warmup_node, blueprint),
        ctx.run_node(vocabulary_node, blueprint),
        ctx.run_node(key_points_node, blueprint),
        ctx.run_node(self_assessment_node, blueprint),
    )

    # Stage 2 — Wave 2 (parallel, blueprint only)
    wave2_results = await asyncio.gather(
        ctx.run_node(core_explainer_node, blueprint),
        *[ctx.run_node(subconcept_node, (blueprint, i))
          for i in range(len(blueprint.sub_competencies))],
        ctx.run_node(strategy_list_node, blueprint),
        ctx.run_node(deep_dive_node, blueprint),
        ctx.run_node(model_passage_node, blueprint),
        ctx.run_node(assessment_passage_node, blueprint),
    )

    # Stage 2 — Wave 3 (sequential dependencies within wave)
    model_passage, assessment_passage = wave2_results[-2], wave2_results[-1]
    check_in = await ctx.run_node(check_in_node, (blueprint, model_passage))
    assessment_questions = await ctx.run_node(
        assessment_questions_node, (blueprint, assessment_passage)
    )
    step_up = await ctx.run_node(
        step_up_node, (blueprint, assessment_passage, assessment_questions)
    )

    # Stage 3 — answer key (always last)
    answer_key = await ctx.run_node(
        answer_key_node, (blueprint, check_in, assessment_questions)
    )

    # Stage 4 — validate; retry failed sections once
    all_sections = {... all section outputs ...}
    validation = await ctx.run_node(validator_node, all_sections)

    retry_count = 0
    while not validation.passed and retry_count < 1:
        for section_key in validation.failed_sections:
            # ctx.run_node with a new node instance forces re-execution
            # even though the original node was checkpointed
            all_sections[section_key] = await ctx.run_node(
                retry_node_for(section_key, validation.failures[section_key]),
                (blueprint, all_sections),
            )
        validation = await ctx.run_node(validator_node, all_sections)
        retry_count += 1

    # Stage 5 — render
    return await ctx.run_node(renderer_node, (blueprint, all_sections, validation))


root_agent = Workflow(
    name="study_guide_generator",
    edges=[("START", study_guide_workflow)],
)
```

### Execution waves

| Wave | Nodes                                                                                                  | Runs via                                                                                |
| ---- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| 0    | `blueprint_node`                                                                                       | `await ctx.run_node()` — sequential                                                     |
| 1    | `intro`, `learning_targets`, `warmup`, `vocabulary`, `key_points`, `self_assessment`                   | `asyncio.gather()` — parallel                                                           |
| 2    | `core_explainer`, `subconcept` ×N, `strategy_list`, `deep_dive`, `model_passage`, `assessment_passage` | `asyncio.gather()` — parallel                                                           |
| 3    | `check_in`, `assessment_questions`, `step_up`                                                          | mixed — `check_in` and `assessment_questions` parallel; `step_up` sequential after both |
| 4    | `answer_key`                                                                                           | `await ctx.run_node()` — sequential, always last                                        |
| 5    | `validator`                                                                                            | `await ctx.run_node()` — sequential                                                     |
| 6    | retry loop (failed sections only)                                                                      | `while` loop + `ctx.run_node()` — one retry per failed section                          |
| 7    | `renderer`                                                                                             | `await ctx.run_node()` — sequential                                                     |

---

## 5. Workflow nodes reference

### blueprint_node

Decorated with `@node`. Reads the `GenerateRequest` from its input, builds the system prompt and blueprint prompt, calls Gemini, validates and returns a `Blueprint` object. All subsequent nodes receive the blueprint as part of their input — it is never stored in a separate session state object; instead `ctx.run_node()` passes it directly as a function argument.

### Section generation nodes (Waves 1–4)

Each section node is a `@node`-decorated function following this pattern:

1. Receive `blueprint` (and any dependency outputs) as input from `ctx.run_node()`
2. Build a section-specific prompt using the corresponding template from `prompts/templates/`
3. Call Gemini 2.0 Flash with `response_mime_type="application/json"`
4. Parse and structurally validate the JSON response (schema check only — content validation happens in the validator node)
5. Return the parsed dict

Because `ctx.run_node()` returns outputs directly, there is no session state dictionary to read from or write to. Dependency data is threaded through function arguments by the `study_guide_workflow` orchestrator node.

The `subconcept_node` is called once per sub-competency using a list comprehension inside `asyncio.gather()`. The orchestrator node handles this loop — not a framework-level `LoopNode`.

The `answer_key_node` explicitly receives `check_in`, `assessment_questions`, and `assessment_passage` outputs as inputs. It is the only node that assembles cross-section content.

### validator_node

Decorated with `@node`. Receives all section outputs as a dict. Runs all hard and soft validators. Returns a `ValidationResult`. Does not raise exceptions — all failures are captured in the return value.

### retry_node_for(section_key, failure_messages)

Not a fixed node — the orchestrator creates a new node instance per failed section using a factory function. The retry node uses the same prompt template as the original generation pass, includes the specific validator failure message in the retry prompt, and calls the shared Gemini wrapper with `TEMP_RETRY`. This gives Gemini targeted correction guidance while keeping retries conservative.

Because each retry node is a new instance with a distinct name, ADK's checkpointing system treats it as a fresh execution rather than skipping it as already-completed.

### renderer_node

Decorated with `@node`. Receives blueprint, all section outputs, and validation result. Produces two outputs: a base64-encoded PDF binary (via Jinja2 + WeasyPrint) and a `WebPreviewPayload` JSON object for the React frontend. Returns both as a single dict.

Both outputs are returned to the frontend in the final response payload.

---

## 6. Data contracts

All contracts are defined as Pydantic models in `backend/study-guide-agent/app/types.py` and mirrored as TypeScript interfaces in `frontend/lib/types.ts`. The JSON schema is the source of truth.

### GenerateRequest

Sent from the frontend to the ADK backend as the initial payload.

```
GenerateRequest
  lesson_metadata:
    subject: string
    grade_level: int (1–12)
    market: string ("PH" | "JP" | "VN" | free text)
    language: string (default "en")
    unit_number: int
    unit_title: string
    lesson_number: int
    lesson_title: string
    lesson_code: string
  curriculum:
    competency_code: string
    competency_description: string
    sub_competencies: SubCompetency[]
      id: string
      label: string
  instructional_design:
    core_concept: string
    bloom_targets: string[3]
    essential_question_seed: string
  optional:
    vocabulary_seeds?: string[]
    topic_domains?: Record<string, string>
    tone_register?: string (default "warm-formal")
    length_preset?: "short" | "standard" | "long" (default "standard")
```

### PromptLabGenerateRequest

Used only by the private reviewer prompt-lab flow. This contract wraps the existing study-guide request and adds temporary prompt overrides for the current run.

```
PromptLabGenerateRequest
  base_request: GenerateRequest
  prompt_overrides:
    system_prompt_append?: string
    section_overrides?: Record<string, string>
      # keyed by supported section key such as
      # intro, warmup, vocabulary, core_explainer, model_passage, etc.
  sample_case_id?: string
  reviewer_label?: string
```

Rules:

- `base_request` remains the same canonical lesson input shape used by the teacher-facing generator.
- `prompt_overrides` are request-scoped only; they do not mutate the default prompt templates on disk.
- Unsupported section keys are rejected by the backend with a clear validation error.
- The prompt-lab MVP may support only a subset of section overrides initially, but that supported allowlist must be explicit in code and UI.

### Blueprint

Returned by the blueprint node and passed by the orchestrator to all dependent section nodes as a function argument.

```
Blueprint
  lesson_id: string
  title: string
  essential_question: string
  introduction_hook: string
  learning_targets: LearningTarget[]
    number: int
    bloom_verb: string
    objective: string
  vocabulary: VocabEntry[]
    word: string
    definition: string
    example_sentence: string
  topic_domains:
    model_passage: string
    assessment_passage: string   # must differ from model_passage
    entertain_example: string
    inform_example: string
    persuade_example: string
  sub_competencies: SubCompetency[]
  core_concept: string
```

### GenerateResponse

Returned from ADK backend to the Next.js proxy on completion.

```
ValidationResult
  passed: bool
  failed_sections: string[]      # sections that failed the latest validation pass
  failures: Record<string, string[]>
                                 # per-section hard validation failure messages
  warnings: string[]             # soft validator warnings to surface in UI
  best_effort_sections: string[] # sections included despite unresolved retry failure
```

```
GenerateResponse
  success: bool
  pdf_base64: string              # base64-encoded PDF binary
  preview: WebPreviewPayload      # structured section data for React preview
    sections: PreviewSection[]
      section_id: string
      section_type: string
      title: string
      icon_key?: string           # optional renderer-selected icon token for section-level visual affordances
      content: object             # shape varies by section_type; documented per-section
  validation: ValidationResult
  error?: string                  # present only on failure
```

The prompt-lab MVP reuses `GenerateResponse` for generation results so reviewers see the same preview, PDF, and validation shape as the teacher-facing flow. No separate result schema is required for the first version.

### ProgressEvent

Streamed from the Next.js proxy to the browser via SSE during generation.

```
ProgressEvent
  type: "node_started" | "node_complete" | "validation_started"
       | "retry_started" | "render_started" | "done" | "error"
  node: string                    # e.g. "blueprint", "intro", "validator"
  message?: string
  timestamp: ISO8601 string
```

---

## 7. Validation layer

### Hard validators

Hard validators block document assembly. A section that fails a hard validator is retried once. If the retry also fails, the document is assembled with a visible warning on the affected section.

| Validator                       | What it checks                                                                                                 | Section(s) it applies to       |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| `vocab_presence`                | Every vocabulary word from the blueprint appears (case-insensitive) in the combined body section text          | All body sections collectively |
| `self_assess_targets`           | Each skill row in the self-assessment matches a learning target objective verbatim                             | `self_assessment`              |
| `answer_key_quotes`             | Each assessment answer evidence quote in the answer key contains a verbatim phrase from the assessment passage | `answer_key`                   |
| `assessment_question_grounding` | Each assessment question evidence hint stays grounded to the assessment passage, including location-style, author-purpose, and other question-aligned guidance hints that still point students to passage-supported content | `assessment_questions`         |
| `passage_domain_diff`           | The topic domain of the assessment passage differs from the model passage domain                               | `assessment_passage`           |
| `json_schema`                   | Each section output parses correctly against its expected JSON schema                                          | All section nodes              |

### Soft validators

Soft validators produce warnings that are surfaced to the user in the web preview but do not block assembly or trigger retries.

| Validator        | What it checks                                                                                                                                |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `answer_leakage` | Instructional body sections do not contain verbatim phrases that appear in the answer key possible answers; assessment artifacts are excluded |
| `reading_level`  | Longer prose-heavy sections stay within the configured grade-band tolerance, with warnings when a section is materially above or below target |

### Retry logic

When the validator node returns `passed=False`, the `study_guide_workflow` orchestrator node enters a `while` loop. For each section key in `validation.failed_sections`, it calls `ctx.run_node()` with a retry node instance created by the `retry_node_for()` factory. The retry node includes the specific validator failure message in the retry prompt and regenerates with `TEMP_RETRY = 0.3`, giving Gemini targeted correction guidance rather than regenerating blindly.

After all failed sections are retried, the validator runs a second time. The `while` loop condition limits retries to one pass — on a second failure the section is included as `best_effort` in the final `ValidationResult` and the warning is surfaced to the user in the web preview.

Because ADK dynamic workflows checkpoint each node execution by deterministic execution ID, a mid-run timeout or infrastructure failure resumes from the last successful node — not from the start of the workflow.

### Presentation-only visual affordances

Icons are presentation metadata, not instructional content. They do not participate in prompt generation, hard validation, or retry decisions. If icon resolution fails for a section or UI role, the renderer and preview fall back to text-only output rather than failing the guide generation run.

---

## 8. Rendering pipeline

The renderer node runs after all sections have passed validation (or been flagged as best-effort). It produces two outputs in parallel.

### PDF rendering

The renderer populates a Jinja2 HTML template with the validated section content, then passes the rendered HTML to WeasyPrint to produce a PDF binary. The HTML template defines:

- Page margins and size (A4)
- Section order (hardcoded in the template — matches the fixed 17-section structure)
- Heading hierarchy (H1 for the lesson title, H2 for section titles, H3 for sub-concept titles)
- Deterministic icon slots beside section titles, selected subheaders, and repeated callout treatments using a backend-owned icon allowlist
- Table structures for vocabulary (4 columns: word, part of speech, definition, example) and self-assessment (skill × 3 confidence columns)
- Page break rules: the answer key always begins on a new page; the assessment passage begins on a new page
- House style CSS: font family, font sizes per grade band, line height, colour palette

### Iconography system

The first visualization enhancement is a controlled icon system rather than generated media. The iconography design has these constraints:

- Icons are selected deterministically from a fixed allowlist keyed by section type and UI role; Gemini does not generate icon choices.
- Initial scope covers section headers, selected subsection headings, and recurring callouts such as warnings, tips, or assessment markers.
- PDF rendering uses template-owned inline SVG or equivalent renderer-controlled markup so icons survive WeasyPrint reliably.
- Web preview consumes an optional `icon_key` emitted by the renderer and maps it to a local React icon component with the same semantic meaning.
- Unknown or unsupported `icon_key` values degrade gracefully to text-only rendering and do not trigger validation failures.

### Web preview rendering

The renderer also produces a `WebPreviewPayload` JSON object that mirrors the PDF structure but is shaped for React consumption. Each section in the payload includes its `section_type`, a `title`, an optional `icon_key`, and a `content` object whose shape is documented per-section type. The React `WebPreview` component maps `section_type` to a dedicated sub-component that handles the rendering of that section's specific content structure (e.g. `VocabularySection` renders a table, `PassageSection` renders styled paragraphs with annotations) while using `icon_key` to render the same high-level visual affordance family used in the PDF.

---

## 9. Frontend architecture

### Page structure

The application is a single-page experience on `app/page.tsx`. It has two states: the input form (pre-generation) and the results view (post-generation). The transition between them is managed by a top-level `useState` tracking the generation stage.

### Input form

`InputForm.tsx` is a fully controlled form with four field groups:

- **Lesson metadata** — subject, grade level, market, language, unit, lesson identifiers
- **Curriculum** — competency code, description, and a dynamic sub-competency list (add/remove rows)
- **Instructional design** — core concept, three Bloom targets, essential question seed
- **Optional inputs** — collapsible; vocabulary seeds, topic domain overrides, tone register, length preset

On submit, the form serialises to a `GenerateRequest` and POSTs to `app/api/generate/route.ts`.

### Prompt-lab reviewer page

`app/prompt-lab/page.tsx` is a separate internal-only page for non-technical reviewers. It is not part of the normal teacher-facing landing page and should be hidden from general product navigation in the MVP.

The prompt-lab page should provide:

- a sample-input selector backed by a small curated set of lesson cases
- a simplified form or preloaded request editor for the underlying `GenerateRequest`
- plain-text editors for prompt override fields scoped to the supported section allowlist
- a generate action that POSTs a `PromptLabGenerateRequest` to a dedicated proxy route
- the same progress, preview, download, and validation-warning experience already used by the main generation flow

The MVP does not require in-UI publishing, approval, or multi-user collaboration. It is a reviewer sandbox for evaluating prompt wording against real study-guide output.

### Progress tracker

`ProgressTracker.tsx` consumes the SSE stream from the API proxy and renders a vertical step list. Each `node_complete` event checks off the corresponding step. The tracker shows the current active node and elapsed time.

### Results view

On `done` event receipt, the results view renders two tabs: **Web Preview** and **Download PDF**.

The Web Preview tab renders `WebPreview.tsx`, which maps the `WebPreviewPayload` sections to their respective React sub-components. Soft validator warnings are displayed as amber inline callouts on the affected sections. Best-effort sections are marked with a visible badge. Section-level iconography should visually track the PDF treatment so teachers do not see two different visual languages for the same generated guide.

The Download PDF tab renders `DownloadButton.tsx`, which decodes the `pdf_base64` field and triggers a browser file download.

### API proxy route

`app/api/generate/route.ts` is a thin proxy. It forwards the `GenerateRequest` to the ADK backend, receives the SSE stream, and re-streams `ProgressEvent` objects to the browser. On completion it attaches the final `GenerateResponse` as a final SSE event. This layer exists to avoid exposing the ADK backend URL to the browser and to handle CORS and auth headers centrally.

The prompt-lab flow uses a separate thin proxy route, for example `app/api/prompt-lab/generate/route.ts`, so reviewer-only request handling stays isolated from the public teacher path. That route forwards `PromptLabGenerateRequest` to a matching backend endpoint, re-streams the same `ProgressEvent` contract, and returns the same `GenerateResponse` shape on completion.

The backend implementation must continue to use the same workflow orchestration, validators, and renderer. The only prompt-lab-specific behavior is the request-scoped prompt override layer applied when building the system prompt and supported section prompts.

---

## 10. Deployment architecture

### Recommended topology

The recommended deployment shape remains a split stack:

- **Frontend:** Firebase App Hosting for the Next.js 14 application and its thin API proxy route
- **Backend:** Google Cloud Run for the Python ADK service and WeasyPrint renderer

This remains the best default for the current repo because it matches the runtime split already designed into the app, keeps the backend on the infrastructure that ADK tooling targets most directly, and preserves the current Next.js server-route runtime without rewriting the frontend into a static-hosting shape.

### Environment modes

The repo should support four operating modes:

| Mode           | Frontend runtime                                                          | Backend runtime                                          | Primary purpose                                             |
| -------------- | ------------------------------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------- |
| Fast local dev | `npm run dev`                                                             | `uv run uvicorn app.fast_api_app:app --reload`           | Fast feature iteration                                      |
| Local parity   | `next build && next start` or equivalent production-mode frontend runtime | Same container image intended for Cloud Run, run locally | Reproducing deployment-only bugs                            |
| Remote staging | Firebase App Hosting staging environment                                  | Separate non-production Cloud Run service                | Early deployment checks after key implementation milestones |
| Production     | Firebase App Hosting production environment                               | Cloud Run production service                             | End-user traffic                                            |

Across all four modes, the application contract stays the same: the frontend talks only to the backend URL configured through `ADK_BACKEND_URL`, and the backend owns Gemini access, validation, and PDF rendering.

### Fast local development

```mermaid
flowchart LR
    Browser --> NextJS["Next.js dev server\nlocalhost:3000"]
    NextJS --> ADK["Scaffolded backend server\nlocalhost:8000\n(uv run uvicorn app.fast_api_app:app)"]
    ADK --> Gemini["Gemini 2.0 Flash\n(Google API)"]
```

Next.js and the ADK backend run as separate local processes. The Next.js API proxy reads `ADK_BACKEND_URL=http://localhost:8000` from `frontend/.env.local` and forwards requests there. No cloud infrastructure required.

### Local parity mode

For deployment debugging, the repo should also support a production-like local mode where:

- the backend runs from the same container image configuration intended for Cloud Run
- the frontend runs in production mode rather than the hot-reload dev server
- the request path stays the same as remote usage: browser -> Next.js -> ADK backend
- environment values are injected through the same variables and secret names used remotely, with local overrides only where URLs differ

This mode is slower than normal development and should not replace the default local loop. Its purpose is parity, not iteration speed.

### Managed cloud deployment

```mermaid
flowchart LR
  Browser --> AppHosting["Firebase App Hosting\n(Next.js)"]
  AppHosting --> CloudRun["Google Cloud Run\n(ADK backend)"]
    CloudRun --> Gemini["Gemini 2.0 Flash\n(Google API)"]
```

The ADK backend is containerised and deployed to Google Cloud Run. The Next.js frontend is deployed to Firebase App Hosting. The same frontend proxy architecture is preserved in local and remote environments; the main environment-level change is the value of `ADK_BACKEND_URL`:

| Environment    | `ADK_BACKEND_URL` value                        |
| -------------- | ---------------------------------------------- |
| Local dev      | `http://localhost:8000`                        |
| Local parity   | local backend URL exposed by the parity stack  |
| Remote staging | `https://<staging-service>.run.app`            |
| Production     | `https://your-service.run.app` (Cloud Run URL) |

**No proxy architecture change is required** — the Next.js API route forwards requests to whatever URL `ADK_BACKEND_URL` points to. The frontend code should stay identical across fast local dev, parity mode, remote dev, and production.

**CORS:** The ADK backend must be configured to accept requests from the Firebase App Hosting domains used for staging and production. In parity mode and local dev, allow the local frontend origin as well. Configure allowed origins in the backend server startup rather than relying on infrastructure defaults.

**Runtime fit:** Cloud Run handles autoscaling and supports long-running requests (up to 3600 seconds), which is required for the 30–90 second generation window and PDF rendering path.

**Operational rule:** deployment testing should happen in stages, not only at the end of the project. The recommended checkpoints are after backend orchestration is usable, after frontend proxy and streaming are usable, and again after end-to-end QA passes.

For the prompt-lab MVP, the intended remote environment is a private staging or internal deployment rather than the public production teacher flow. The prompt-lab page may share the same deployed frontend and backend services as staging, but access to the page should be limited operationally rather than exposing it as a public product route.

---

## 11. Key design decisions and alternatives considered

### Decision: ADK dynamic workflow over ADK graph-based workflow

ADK 2.0 offers two workflow styles. Graph-based workflows (`Workflow` + `edges` array + `JoinNode`) are appropriate for simple linear or branching pipelines where all paths are known at design time. Dynamic workflows (`@node` + `ctx.run_node()` + plain Python) are chosen here for three reasons:

**Retry logic is a `while` loop, not 16 explicit retry edges.** In a graph-based workflow, routing only failed sections to retry nodes requires an `Event(route=...)` per section and a corresponding entry in the `edges` array — one route per section type, or 16+ entries. In a dynamic workflow, the same logic is `while not validation.passed: for s in failed: await ctx.run_node(retry_node_for(s))`. The intent is immediately readable.

**Wave parallelism is `asyncio.gather()`.** Graph-based fan-out requires a `JoinNode` per wave and careful `edges` construction. `asyncio.gather()` is standard Python and needs no framework primitives.

**Automatic checkpointing covers the retry case.** Dynamic workflow nodes are checkpointed by deterministic execution ID. On resume after a timeout, already-completed nodes are skipped. This means the retry-on-failure behaviour is a natural consequence of how dynamic workflows resume, not an extra feature to implement.

**Alternative considered:** ADK graph-based workflow. Rejected because the `edges` array at 16+ sections with per-section retry routes becomes unwieldy and harder to read than the equivalent Python code.

### Decision: ADK dynamic workflow over plain async orchestrator

A plain `async def orchestrate()` function in Next.js resolves section dependencies and runs waves correctly, but has no durable state. A mid-run timeout discards all completed outputs and the entire guide must restart. ADK dynamic workflows checkpoint every `ctx.run_node()` call, so a timeout resumes from the last successful node.

**Alternative considered:** Plain Next.js orchestrator with Redis for state persistence. Rejected because it replicates ADK's checkpointing in application code with no technical advantage.

### Decision: Firebase App Hosting for frontend and Cloud Run for backend

The current recommended managed topology is Firebase App Hosting for the Next.js frontend and Google Cloud Run for the Python ADK backend.

This split matches the existing architecture cleanly:

- the frontend stays on a managed platform that supports the current Next.js server runtime and app-router proxy routes
- the backend stays on a platform that matches the Python container, ADK deployment path, and WeasyPrint runtime needs
- local and remote environments can keep the same browser -> Next.js -> backend request flow, which is better for reproducibility than switching to a different transport in production

**Alternative considered:** Cloud Run for both frontend and backend. Rejected for now because it increases operational burden on the Next.js side without solving a current product constraint better than Firebase App Hosting for the current staging-first rollout.

**Alternative considered:** Direct browser calls from the frontend to the Cloud Run backend in production. Rejected for now because the thin Next.js proxy keeps the frontend request surface stable across environments and avoids coupling browser clients to backend origin changes. Revisit only if the proxy route proves to be the actual bottleneck under deployed streaming tests.

### Decision: Single validation pass after all sections complete, not per-section inline validation

After each section generates, a structural JSON schema check runs immediately (cheap, catches malformed Gemini responses). The full content validation runs once after all sections complete. This is the correct order because most hard validators are cross-section: vocab presence requires all body sections; answer leakage requires the answer key to exist first.

**Alternative considered:** Per-section validation inline. Rejected because cross-section validators cannot run per-section by definition, and it would produce a more complex workflow that is harder to reason about.

### Decision: WeasyPrint for PDF rendering over Puppeteer

WeasyPrint renders HTML/CSS → PDF server-side in the Python ADK process. The Jinja2 template it uses is also the canonical section-order and layout spec. Puppeteer has better CSS support but requires a full Chrome binary in the Docker image, significantly increasing container size and Cloud Run cold start time.

### Decision: Web preview from structured JSON, not from the PDF

The web preview is rendered from the same structured JSON that feeds the PDF renderer. This means the preview is available immediately on generation completion, without waiting for PDF rendering. Soft validator warnings are attached to the structured JSON, so they can be displayed precisely on the affected section in the React preview.

### Decision: SSE over WebSockets for progress streaming

Generation takes 30–90 seconds. SSE provides one-directional server-to-browser streaming with no additional library and is sufficient because the browser never needs to send messages back during generation.

### Decision: `ADK_BACKEND_URL` environment variable over a separate proxy service

The Next.js API route reads `ADK_BACKEND_URL` and forwards requests directly. In local dev this is `http://localhost:8000`; in managed staging or production it is the Cloud Run URL. No separate proxy service, gateway, or network configuration change is required when moving between environments. The only addition for managed environments is CORS configuration on the ADK backend allowing the Firebase App Hosting domain.

### Decision: Request-scoped prompt overrides over direct prompt-file editing by reviewers

The prompt-lab MVP should treat reviewer edits as request-scoped prompt overrides rather than direct writes to prompt template files. This keeps non-technical reviewers out of the repository, preserves a stable default prompt path for the teacher-facing product, and allows the same generation workflow to be exercised safely in a staging environment.

**Alternative considered:** exposing prompt template files or a prompt-pack file editor directly to reviewers. Rejected for the MVP because remote reviewers do not have repo access, and direct file editing would couple reviewer experiments to source control and deployment state too tightly.
