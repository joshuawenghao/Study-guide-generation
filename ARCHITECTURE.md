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

The frontend and backend communicate over a single HTTP endpoint. The frontend sends a structured lesson request and streams progress events back; the backend runs the full graph and returns a completed PDF and a structured web preview payload.

```
┌─────────────────────────────┐        ┌──────────────────────────────────────┐
│        Next.js frontend      │        │           ADK backend                │
│                             │        │                                      │
│  ┌─────────────────────┐   │  POST  │  ┌────────────────────────────────┐  │
│  │   Input form         │──────────▶│  │    ADK agent graph             │  │
│  │  (lesson metadata,   │   /gen    │  │    (graph-based workflow)      │  │
│  │   curriculum, etc.)  │          │  │                                │  │
│  └─────────────────────┘   │        │  │  blueprint → sections →        │  │
│                             │◀───────│  │  validate → retry? → render   │  │
│  ┌─────────────────────┐   │  SSE   │  │                                │  │
│  │  Progress tracker    │   │        │  └────────────────────────────────┘  │
│  │  Web preview         │   │        │                                      │
│  │  PDF download        │   │        │  Gemini 2.0 Flash (all LLM calls)    │
│  └─────────────────────┘   │        └──────────────────────────────────────┘
└─────────────────────────────┘
```

---

## 2. Tech stack decisions

| Layer | Choice | Reason |
|---|---|---|
| Frontend framework | Next.js 14 (App Router) | Single repo for UI and API proxy; SSE streaming support built in |
| Styling | Tailwind CSS | Utility-first, no design system overhead for a prototype |
| Agent framework | Google ADK 2.0 (Python) | Graph-based workflow with durable state; native Gemini integration; conditional edge routing for validation retry |
| LLM | Gemini 2.0 Flash | Best cost/latency ratio for 17 sequential/parallel calls; ADK has first-class Gemini support |
| PDF rendering | WeasyPrint (Python) | HTML/CSS → PDF with full layout control; runs server-side in the ADK process |
| Web preview | Structured JSON → React components | Preview is assembled from the same section JSON that feeds the PDF renderer |
| Deployment (Phase 1) | Local — Next.js dev server + ADK local runner | Fastest iteration loop; no infrastructure required |
| Deployment (Phase 2) | Vercel (frontend) + Google Cloud Run (ADK) | ADK deploys natively to Cloud Run; Vercel handles Next.js with zero config |

### Why ADK over a plain Next.js orchestrator

A plain async orchestrator (as considered earlier) is sufficient when the pipeline is fully static. ADK is chosen here for three specific reasons that map to IFC criteria:

1. **Durable workflow state.** ADK persists graph state between node executions. If a section generation call times out or fails, the graph resumes from the last committed node rather than restarting from scratch. This directly satisfies the *automated retry on validation failure* must-have without hand-rolling state management.

2. **Conditional edge routing.** After the validation node runs, ADK graph edges can conditionally route only failed sections back to their respective generation nodes. This is a first-class graph feature — not a workaround built on `if` statements in application code.

3. **Future agent extensibility.** The IFC nice-to-have for deployment to managed infrastructure is satisfied by ADK's native Cloud Run deployment path. Adding a reading-level validator agent or a curriculum alignment agent later requires registering a new node, not restructuring the pipeline.

---

## 3. Repository structure

```
/
├── frontend/                        # Next.js 14 application
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                 # Input form + generation UI
│   │   └── api/
│   │       └── generate/
│   │           └── route.ts         # Proxy to ADK backend + SSE stream
│   ├── components/
│   │   ├── InputForm.tsx
│   │   ├── ProgressTracker.tsx
│   │   ├── WebPreview.tsx           # Renders section JSON as styled HTML
│   │   └── DownloadButton.tsx
│   ├── lib/
│   │   └── types.ts                 # Shared TypeScript types (mirrored from backend)
│   └── package.json
│
└── backend/                         # ADK agent (Python)
    ├── agent.py                     # ADK graph definition — the single source of truth
    ├── nodes/
    │   ├── blueprint.py             # Node: generate blueprint JSON
    │   ├── sections/
    │   │   ├── intro.py
    │   │   ├── learning_targets.py
    │   │   ├── warmup.py
    │   │   ├── vocabulary.py
    │   │   ├── core_explainer.py
    │   │   ├── subconcept.py        # Called once per sub-competency
    │   │   ├── strategy_list.py
    │   │   ├── deep_dive.py
    │   │   ├── model_passage.py
    │   │   ├── check_in.py          # Depends on: model_passage
    │   │   ├── key_points.py
    │   │   ├── assessment_passage.py
    │   │   ├── assessment_questions.py  # Depends on: assessment_passage
    │   │   ├── step_up.py           # Depends on: assessment_questions
    │   │   ├── self_assessment.py
    │   │   └── answer_key.py        # Always last; depends on all question sections
    │   ├── validator.py             # Node: runs all hard + soft validators
    │   └── renderer.py              # Node: assembles validated JSON → PDF + preview JSON
    ├── prompts/
    │   ├── system_prompt.py         # Global system prompt builder (market, grade, subject)
    │   └── templates/               # One prompt template function per section type
    ├── validators/
    │   ├── hard/
    │   │   ├── vocab_presence.py
    │   │   ├── self_assess_targets.py
    │   │   ├── answer_key_quotes.py
    │   │   └── passage_domain_diff.py
    │   └── soft/
    │       ├── answer_leakage.py
    │       └── reading_level.py
    ├── types.py                     # Pydantic models for all data contracts
    └── requirements.txt
```

The frontend and backend are separated into distinct directories because the ADK backend is Python and the frontend is TypeScript. They share no runtime but mirror their data contracts through a common JSON schema documented in section 6.

---

## 4. ADK agent graph

This is the central design of the system. The graph encodes the full generation, validation, and retry workflow as a directed graph with conditional edges.

### Graph diagram

```
                    ┌─────────────┐
                    │  START node  │
                    │ (input form  │
                    │  payload)    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  blueprint  │
                    │   node      │
                    └──────┬──────┘
                           │ blueprint JSON written to session state
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
   ┌─────────┐      ┌─────────┐      ┌─────────────┐      (Wave 1 — no dependencies)
   │  intro  │      │ targets │      │   warmup    │  ...
   └────┬────┘      └────┬────┘      └──────┬──────┘
        │                │                  │
        └────────────────┼──────────────────┘
                         │ all Wave 1 sections complete
                         ▼
              ┌──────────────────┐
              │   model_passage  │             (Wave 2 — no cross-dependencies)
              │  assess_passage  │
              │  core_explainer  │  ...
              └────────┬─────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      ┌────────┐  ┌──────────┐  ┌──────────┐  (Wave 3 — depend on Wave 2)
      │check_in│  │assess_Qs │  │ step_up  │
      └────┬───┘  └─────┬────┘  └────┬─────┘
           └────────────┼────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │   answer_key    │             (Always last)
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │    VALIDATOR    │
               │      node       │
               └────────┬────────┘
                        │
            ┌───────────┴────────────┐
            │ conditional edge       │
            ▼                        ▼
   [all sections pass]       [one or more sections fail]
            │                        │
            ▼                        │ routes only to failed section nodes
   ┌─────────────────┐               │
   │    RENDERER     │    ┌──────────┴────────────┐
   │      node       │    │  targeted retry nodes  │
   │ (PDF + preview) │    │  (one per failed sect) │
   └────────┬────────┘    └──────────┬────────────┘
            │                        │
            ▼                        ▼
      ┌──────────┐          ┌─────────────────┐
      │  output  │          │  VALIDATOR node  │
      │ (PDF +   │          │  (second pass)   │
      │  preview │          └────────┬─────────┘
      │  JSON)   │                   │
      └──────────┘                   ▼
                              [pass → RENDERER]
                              [fail → surface warning,
                               proceed with best output]
```

### Graph node execution model

The graph uses ADK's `ParallelNode` for sections within the same wave and `SequentialNode` dependencies for sections that require prior outputs. The validation node uses ADK's conditional edge API to route only failed sections to retry nodes rather than re-running the full graph.

Session state is the shared data store across all nodes. Each generation node reads from session state (the blueprint and any dependency outputs) and writes its result back to session state under its section key. The validator node reads all section keys, the renderer node reads all section keys and the blueprint.

### Execution waves

| Wave | Nodes | Dependency |
|---|---|---|
| 0 | `blueprint` | None — runs first, always |
| 1 | `intro`, `learning_targets`, `warmup`, `vocabulary`, `key_points`, `self_assessment` | Blueprint only |
| 2 | `core_explainer`, `subconcept` ×N, `strategy_list`, `deep_dive`, `model_passage`, `assessment_passage` | Blueprint only |
| 3 | `check_in`, `assessment_questions`, `step_up` | Wave 2 outputs (`model_passage`, `assessment_passage`) |
| 4 | `answer_key` | All question-bearing sections from Waves 1–3 |
| 5 | `validator` | All section outputs |
| 6 | `renderer` (conditional on validation pass) or targeted retry nodes | Validator output |

---

## 5. Graph nodes reference

### blueprint node

Reads the raw lesson request from session state. Produces a `Blueprint` JSON object containing: essential question, learning targets, vocabulary list, topic domains, and sub-competency labels. Every subsequent node reads from the blueprint rather than the raw request — this is the single shared context object for the entire run.

### Section generation nodes (Waves 1–4)

Each section node follows the same pattern:

1. Read blueprint and any dependency outputs from session state.
2. Build a section-specific prompt using the corresponding template from `prompts/templates/`.
3. Call Gemini 2.0 Flash via ADK's built-in model integration with `responseMimeType: application/json`.
4. Parse and lightly validate the JSON schema of the response (structural check only — content validation happens in the validator node).
5. Write the parsed output to session state under the section's key.

The `subconcept` node is called once per sub-competency entry in the blueprint. ADK's `LoopNode` manages this iteration so the graph definition does not hard-code the number of sub-competencies.

The `answer_key` node explicitly reads the outputs of `check_in`, `assessment_questions`, and `step_up` in addition to the blueprint. It is the only node that assembles cross-section content, which is why it runs last and why answer leakage validation focuses on its output.

### validator node

Runs after all generation nodes are complete. Executes all hard validators and soft validators in sequence against the full session state. Writes a `ValidationResult` object to session state with the following shape:

```python
ValidationResult:
  passed: bool                          # True only if all hard validators pass
  failed_sections: list[str]            # Section keys that failed a hard validator
  failures: dict[str, list[str]]        # section_key → list of failure messages
  warnings: list[str]                   # Soft validator warnings (non-blocking)
```

The conditional edge logic reads `passed` and `failed_sections`. If `passed` is True, the edge routes to the renderer node. If False, edges route to the specific retry nodes listed in `failed_sections` — no other nodes are re-executed.

After a retry pass, the validator runs a second time. On a second failure, the validator sets a `best_effort` flag and routes to the renderer regardless, passing the warnings list for surface display to the user.

### renderer node

Reads the full validated session state and assembles the final output in two formats:

**PDF** — uses WeasyPrint to render a structured HTML template populated with section content into a PDF binary. The HTML template is the canonical layout definition: section order, heading levels, table structures (vocabulary, self-assessment), and page break rules (answer key always starts on a new page) are all defined here.

**Web preview JSON** — a structured JSON object that mirrors the PDF layout, used to render the web preview in the React frontend without re-fetching the PDF. Shape documented in section 6.

Both outputs are written to session state and returned to the frontend in the final response payload.

---

## 6. Data contracts

All contracts are defined as Pydantic models in `backend/types.py` and mirrored as TypeScript interfaces in `frontend/lib/types.ts`. The JSON schema is the source of truth.

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

### Blueprint

Written to session state by the blueprint node. Read by all section nodes.

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
GenerateResponse
  success: bool
  pdf_base64: string              # base64-encoded PDF binary
  preview: WebPreviewPayload      # structured section data for React preview
    sections: PreviewSection[]
      section_id: string
      section_type: string
      title: string
      content: object             # shape varies by section_type; documented per-section
  validation:
    passed: bool
    warnings: string[]            # soft validator warnings to surface in UI
    retried_sections: string[]    # sections that were retried during validation pass
  error?: string                  # present only on failure
```

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

| Validator | What it checks | Section(s) it applies to |
|---|---|---|
| `vocab_presence` | Every vocabulary word from the blueprint appears (case-insensitive) in the combined body section text | All body sections collectively |
| `self_assess_targets` | Each skill row in the self-assessment matches a learning target objective verbatim | `self_assessment` |
| `answer_key_quotes` | Each possible answer in the answer key contains a verbatim phrase from the assessment passage | `answer_key` |
| `passage_domain_diff` | The topic domain of the assessment passage differs from the model passage domain | `assessment_passage` |
| `json_schema` | Each section output parses correctly against its expected JSON schema | All section nodes |

### Soft validators

Soft validators produce warnings that are surfaced to the user in the web preview but do not block assembly or trigger retries.

| Validator | What it checks |
|---|---|
| `answer_leakage` | Body sections do not contain verbatim phrases that appear in the answer key possible answers |
| `reading_level` | Each section's Flesch-Kincaid grade score falls within ±1.0 of the target grade band |

### Retry logic

When the validator node identifies failed sections, ADK's conditional edge routing fires a retry edge only to the generation nodes of failed sections. The retry nodes use the same prompt templates as the original generation pass but append a `RETRY_CONTEXT` block to the user prompt describing the specific constraint that was violated. This gives Gemini targeted correction guidance rather than regenerating blindly.

After the retry pass, the validator runs a second time. The system does not retry more than once per section per run — on a second failure the section is flagged as `best_effort` and the warning is surfaced to the user.

---

## 8. Rendering pipeline

The renderer node runs after all sections have passed validation (or been flagged as best-effort). It produces two outputs in parallel.

### PDF rendering

The renderer populates a Jinja2 HTML template with the validated section content, then passes the rendered HTML to WeasyPrint to produce a PDF binary. The HTML template defines:

- Page margins and size (A4)
- Section order (hardcoded in the template — matches the fixed 17-section structure)
- Heading hierarchy (H1 for the lesson title, H2 for section titles, H3 for sub-concept titles)
- Table structures for vocabulary (4 columns: word, part of speech, definition, example) and self-assessment (skill × 3 confidence columns)
- Page break rules: the answer key always begins on a new page; the assessment passage begins on a new page
- House style CSS: font family, font sizes per grade band, line height, colour palette

### Web preview rendering

The renderer also produces a `WebPreviewPayload` JSON object that mirrors the PDF structure but is shaped for React consumption. Each section in the payload includes its `section_type`, a `title`, and a `content` object whose shape is documented per-section type. The React `WebPreview` component maps `section_type` to a dedicated sub-component that handles the rendering of that section's specific content structure (e.g. `VocabularySection` renders a table, `PassageSection` renders styled paragraphs with annotations).

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

### Progress tracker

`ProgressTracker.tsx` consumes the SSE stream from the API proxy and renders a vertical step list. Each `node_complete` event checks off the corresponding step. The tracker shows the current active node and elapsed time.

### Results view

On `done` event receipt, the results view renders two tabs: **Web Preview** and **Download PDF**.

The Web Preview tab renders `WebPreview.tsx`, which maps the `WebPreviewPayload` sections to their respective React sub-components. Soft validator warnings are displayed as amber inline callouts on the affected sections. Best-effort sections are marked with a visible badge.

The Download PDF tab renders `DownloadButton.tsx`, which decodes the `pdf_base64` field and triggers a browser file download.

### API proxy route

`app/api/generate/route.ts` is a thin proxy. It forwards the `GenerateRequest` to the ADK backend, receives the SSE stream, and re-streams `ProgressEvent` objects to the browser. On completion it attaches the final `GenerateResponse` as a final SSE event. This layer exists to avoid exposing the ADK backend URL to the browser and to handle CORS and auth headers centrally.

---

## 10. Deployment architecture

### Phase 1 — local development

```
Browser → Next.js dev server (localhost:3000) → ADK local runner (localhost:8000)
```

Next.js and the ADK backend run as separate local processes. The Next.js API proxy points to `localhost:8000`. No cloud infrastructure required.

### Phase 2 — production

```
Browser → Vercel (Next.js) → Cloud Run (ADK backend)
```

The ADK backend is containerised using ADK's built-in `adk deploy` tooling and deployed to Google Cloud Run. The Next.js frontend is deployed to Vercel. The API proxy route's target URL is set via an environment variable (`ADK_BACKEND_URL`). Cloud Run handles autoscaling and the long-running generation timeout (up to 3600 seconds per request).

The frontend and backend are deployed and scaled independently. The only shared interface is the JSON API contract documented in section 6.

---

## 11. Key design decisions and alternatives considered

### Decision: ADK graph-based workflow over plain async orchestrator

The plain Next.js orchestrator considered earlier resolves section dependencies correctly but has no durable state — a mid-run timeout discards all completed section outputs and the entire guide must restart. ADK's graph-based workflow commits each node's output to durable session state, so a timeout or retry resumes from the last successful node. This maps directly to the IFC must-have for automated retry on validation failure.

**Alternative considered:** Hand-rolled retry logic in the Next.js orchestrator with Redis for state persistence. Rejected because it replicates ADK's graph management in application code, adding maintenance overhead without a technical advantage.

### Decision: Single validation pass with conditional fan-out, not per-section inline validation

After each section generates, a structural JSON schema check runs immediately (cheap, catches malformed responses early). The full content validation — vocab presence, verbatim quote checks, answer leakage — runs once after all sections are complete. This is the correct order because most hard validators are cross-section checks: vocab presence requires all body sections to be complete before it can pass, and answer leakage requires the answer key to exist before it can be checked.

**Alternative considered:** Per-section validation inline, with each node retrying itself if it fails its own constraints. Rejected because it cannot handle cross-section validators by definition, and produces a more complex graph that is harder to reason about during debugging.

### Decision: WeasyPrint for PDF rendering over a JavaScript PDF library (pdf-lib, Puppeteer)

WeasyPrint renders HTML/CSS → PDF server-side in the Python ADK process. The HTML template that drives it also serves as the canonical layout spec, making it easy to audit the section order, heading hierarchy, and table structure in one place. A JavaScript PDF library (pdf-lib) would require the renderer to be reimplemented in TypeScript and run in the Next.js layer, splitting the pipeline across two runtimes.

**Alternative considered:** Puppeteer (headless Chrome). Has better CSS support than WeasyPrint but requires a full Chrome binary in the Docker image, significantly increasing container size and cold start time on Cloud Run. Rejected for the prototype.

### Decision: Web preview from structured JSON, not from parsing the PDF

The web preview is rendered from the same structured JSON that feeds the PDF renderer, not by extracting content from the PDF after the fact. This means the preview is available immediately when generation completes, without waiting for PDF rendering, and sections with soft validator warnings can be highlighted precisely because the warning is attached to the structured JSON, not to a rendered page.

### Decision: SSE for progress streaming over WebSockets

Generation takes 30–90 seconds. SSE (Server-Sent Events) provides one-directional streaming from server to browser with no additional library, works through Vercel's Edge Runtime, and is sufficient for progress events — the browser never needs to send messages back during generation. WebSockets add bidirectional complexity that is not needed.
