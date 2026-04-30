# Copilot Instructions — Study Guide Generation Web App

This file is read automatically by GitHub Copilot Chat on every conversation in this repository.
Follow all instructions below when generating, editing, or reviewing code for this project.

---

## Project overview

A web app that takes structured lesson inputs from a teacher and generates a complete, curriculum-aligned study guide as a PDF and web preview. Generation is powered by a Google ADK 2.0 agent graph running Gemini 2.0 Flash. The study guide always has a fixed 17-section structure regardless of subject or grade.

Key reference documents (read these before making architectural decisions):
- `IFC.md` — the problem statement, facts, and acceptance criteria
- `ARCHITECTURE.md` — the full system design, graph structure, data contracts, and design decisions

---

## Repository structure

```
/
├── frontend/    # Next.js 14 (App Router), TypeScript, Tailwind CSS
└── backend/     # Python, Google ADK 2.0, Gemini 2.0 Flash, WeasyPrint
```

These are two separate runtimes. They share no code — only a JSON contract documented in `ARCHITECTURE.md` section 6.

---

## Frontend conventions (Next.js / TypeScript)

### General
- Use Next.js 14 App Router only. Never use the Pages Router.
- All components are functional components with hooks. Never use class components.
- TypeScript strict mode is on. Never use `any` — use `unknown` and narrow it, or define a proper type.
- All shared types live in `frontend/lib/types.ts`. Never define types inline in component files.

### Styling
- Use Tailwind CSS utility classes only. Never write custom CSS files or inline `style` props unless Tailwind cannot achieve the result.
- Follow mobile-first responsive design. Use `sm:`, `md:`, `lg:` prefixes for breakpoints.

### Data fetching
- Use `fetch` directly in Server Components or Route Handlers. Do not add axios or any HTTP client library.
- For SSE (Server-Sent Events) streaming from the API proxy, use the native `EventSource` API in the client component. Do not use a library.
- The API proxy route is at `frontend/app/api/generate/route.ts`. It forwards requests to the ADK backend and re-streams progress events. Keep this file thin — no business logic here.

### State management
- Use `useState` and `useReducer` for local state. Do not add Redux, Zustand, or any global state library for the prototype.
- The generation stage is tracked as a discriminated union type:
  ```ts
  type GenerationStage =
    | 'idle'
    | 'planning'
    | 'generating'
    | 'validating'
    | 'rendering'
    | 'done'
    | 'error'
  ```

### Forms
- `InputForm.tsx` is fully controlled. Every field has a corresponding `useState` entry.
- Never use HTML `<form>` with default submit behaviour — always `e.preventDefault()` and handle manually.
- The form serialises to a `GenerateRequest` type on submit. Validate required fields client-side before sending.

### File structure
- One component per file. File name matches the component name exactly.
- Route handlers go in `app/api/[route]/route.ts`. No logic in `page.tsx` beyond rendering and state.

---

## Backend conventions (Python / ADK)

### General
- Python 3.11+. Use type hints everywhere — all function signatures, all class fields.
- Use Pydantic v2 for all data models. All models live in `backend/types.py`. Never define ad-hoc dicts for structured data.
- Use `async`/`await` throughout. All Gemini calls are async. All file I/O is async.
- Never use `print()` for debugging — use the `logging` module with appropriate levels.

### ADK agent graph
- The dynamic workflow definition is the single source of truth for execution order. It lives in `backend/agent.py`.
- The workflow uses ADK 2.0 **dynamic workflows**: `@node` decorator + `ctx.run_node()` + plain Python. Do NOT use graph-based workflow syntax (`edges` array, `JoinNode`, `Event(route=...)`).
- Wave parallelism uses `asyncio.gather()` — not any framework parallel primitive.
- Retry logic for failed sections is a `while` loop calling `ctx.run_node()` with a new retry node instance — not conditional graph edges.
- Every node is a `@node`-decorated function. Nodes receive their inputs as function arguments from `ctx.run_node()` — they do not read from or write to a session state dictionary.
- The `study_guide_workflow` orchestrator node is decorated with `@node(rerun_on_resume=True)` so ADK checkpoints it on resume.

### Gemini calls
- All Gemini calls go through the shared wrapper in `backend/nodes/base.py` (a thin async wrapper around the ADK model client). Never instantiate the Gemini client directly in a node file.
- Always set `response_mime_type="application/json"` for section generation calls.
- Temperature settings per call type:
  - Blueprint: `0.3`
  - Section generation: `0.7`
  - Answer key: `0.3`
  - Retry calls: same temperature as original, with `RETRY_CONTEXT` appended to user prompt
- Max output tokens: `2048` for all calls unless a section has a documented exception.

### Prompt templates
- All prompt templates live in `backend/prompts/templates/`. One file per section type.
- Every template file exports a single function: `def build_prompt(spec, blueprint, request) -> str`
- Prompts must include the output JSON schema inline. Never rely on Gemini inferring the schema.
- Never hardcode market, grade, or subject strings inside a template. Always read from `blueprint` or `request`.

### Validators
- Hard validators live in `backend/validators/hard/`. Soft validators in `backend/validators/soft/`.
- Every validator function signature: `def validate(session_state: dict) -> ValidationResult`
- Hard validators raise nothing — they return a `ValidationResult` with `passed=False` and a list of failure messages. Never use exceptions for validation logic.
- The retry prompt for a failed section must include the specific failure message from the validator, not a generic retry instruction.

### PDF rendering
- The WeasyPrint renderer lives in `backend/nodes/renderer.py`.
- The HTML template lives in `backend/templates/study_guide.html.j2` (Jinja2).
- Section order in the HTML template is the canonical definition of the 17-section order. Never derive section order from anywhere else.
- The answer key section always starts on a new page (`page-break-before: always` in CSS).

---

## Data contracts

The JSON contract between frontend and backend is documented in `ARCHITECTURE.md` section 6.
When changing any field in `backend/types.py`, the corresponding type in `frontend/lib/types.ts` must be updated in the same commit. These must always be in sync.

Key types:
- `GenerateRequest` — sent from frontend to ADK backend
- `Blueprint` — generated by blueprint node, shared across all section nodes via session state
- `GenerateResponse` — returned from ADK backend to frontend on completion
- `ProgressEvent` — streamed via SSE during generation

---

## The 17 fixed sections

The study guide always contains exactly these sections in this order. Never add, remove, or reorder them without updating both `ARCHITECTURE.md` and the HTML renderer template.

| # | Section key | Depends on |
|---|---|---|
| 1 | `intro` | blueprint |
| 2 | `learning_targets` | blueprint |
| 3 | `warmup` | blueprint |
| 4 | `vocabulary` | blueprint |
| 5 | `core_explainer` | blueprint |
| 6 | `subconcept` ×N | blueprint |
| 7 | `strategy_list` | blueprint |
| 8 | `deep_dive` | blueprint |
| 9 | `model_passage` | blueprint |
| 10 | `check_in` | `model_passage` |
| 11 | `key_points` | blueprint |
| 12 | `assessment_passage` | blueprint |
| 13 | `assessment_questions` | `assessment_passage` |
| 14 | `step_up` | `assessment_questions` |
| 15 | `self_assessment` | blueprint |
| 16 | `answer_key` | all question sections |
| 17 | _(rendered separately)_ | answer key |

---

## Hard validation rules

These are non-negotiable constraints. Every hard validator must enforce them:

1. **Vocab presence** — every vocabulary word from the blueprint must appear (case-insensitive) in the combined text of all body sections.
2. **Self-assessment targets** — each skill row in `self_assessment` must match a `learning_targets` objective verbatim.
3. **Answer key quotes** — each possible answer in `answer_key` must contain a verbatim phrase from the `assessment_passage` body.
4. **Passage domain difference** — the topic domain of `assessment_passage` must differ from the topic domain of `model_passage`.
5. **JSON schema** — every section output must parse against its defined Pydantic schema without errors.

---

## What not to do

- Do not add a database or any persistence layer for the prototype.
- Do not add authentication or user accounts for the prototype.
- Do not use LangChain, LangGraph, CrewAI, or any other agent framework — only ADK 2.0.
- Do not use ADK graph-based workflow syntax (`edges` array, `JoinNode`, `Event(route=...)`). Use dynamic workflows only.
- Do not use `SequentialNode`, `LoopNode`, or `ParallelNode` — these do not exist in ADK 2.0's dynamic workflow API.
- Do not read from or write to a session state dictionary in node functions — pass data through `ctx.run_node()` arguments and return values.
- Do not use Puppeteer or headless Chrome for PDF rendering — use WeasyPrint only.
- Do not add WebSockets — use SSE for all streaming.
- Do not call Gemini directly from the frontend under any circumstances.
- Do not store the Gemini API key or any secret in the frontend codebase.
- Do not commit `.env` files. Use `.env.example` files with placeholder values only.

---

## Environment variables

### Frontend (`frontend/.env.local`)
```
ADK_BACKEND_URL=http://localhost:8000   # points to local ADK runner in dev
```

### Backend (`backend/.env`)
```
GEMINI_API_KEY=your_key_here
MARKET_DEFAULT=PH
```

---

## Running locally

```bash
# Backend — run from backend/ (parent of the agent package)
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Copy .env.example to .env inside the agent package and add your API key:
cp study_guide_agent/.env.example study_guide_agent/.env
adk web          # starts ADK dev UI on localhost:8000
                 # select study_guide_agent from the dropdown in the UI

# Frontend
cd frontend
npm install
npm run dev      # starts Next.js on localhost:3000
```
