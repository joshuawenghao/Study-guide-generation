# Claude Code Instructions — Study Guide Generation Web App

This file is loaded automatically by Claude Code on every session in this repository.
Follow all instructions below when generating, editing, or reviewing code for this project.

---

## Project overview

A web app that takes structured lesson inputs from a teacher and generates a complete, curriculum-aligned study guide as a PDF and web preview. Generation is powered by a Google ADK 2.0 agent graph running Gemini 3.5 Flash. The study guide always has a fixed 17-section structure regardless of subject or grade.

Key reference documents (read these before making architectural decisions):

- `IFC.md` — the problem statement, facts, and acceptance criteria
- `ARCHITECTURE.md` — the full system design, graph structure, data contracts, and design decisions
- `TASKS.md` — the canonical implementation plan for the scaffolded repo layout
- `TASK_STATUS.md` — the current completion snapshot and task-by-task status

---

## Repository structure

```
/
├── frontend/    # Next.js 14 (App Router), TypeScript, Tailwind CSS
└── backend/     # Python, Google ADK 2.0, Gemini 3.5 Flash, WeasyPrint
```

These are two separate runtimes. They share no code — only a JSON contract documented in `ARCHITECTURE.md` section 6.

---

## Task tracking

- `TASKS.md` is the stable implementation plan. Do not treat it as a live progress log.
- `TASK_STATUS.md` is the mutable progress snapshot for the current repository state.
- Before implementing new product work, read both `TASKS.md` and `TASK_STATUS.md` to determine what already exists and what can be built on top of it.
- When a task is fully completed, update `TASK_STATUS.md` in the same turn.
- Only mark a task as complete after the implementation exists in the repo and at least one focused validation step has passed.
- If a task is only scaffolded or partially working, mark it as partial rather than complete.

---

## Workspace automation — slash commands

Custom slash commands live in `.claude/commands/`. Invoke them by typing `/command-name` in the chat.

| Command | Purpose |
|---|---|
| `/repo-automation` | Workflow router — decides where to start a session |
| `/spec-groom` | Turns vague requests into implementation-ready spec deltas |
| `/spec-to-tasks` | Converts a settled spec into `TASKS.md` + `TASK_STATUS.md` entries |
| `/task-implement` | Codes one task slice with focused validation |
| `/task-done` | Runs the done gate and updates `TASK_STATUS.md` |
| `/docs-drift` | Reconciles docs with shipped code |

**Standard delivery loop:** `/repo-automation` → `/spec-groom` → `/spec-to-tasks` → `/task-implement` → `/task-done` → `/docs-drift` → repeat

- Start most sessions with `/repo-automation` to route correctly.
- `/task-implement` and `/task-done` are separate — never mark work complete during implementation.
- The repository validation entrypoint is `./scripts/validate-task.sh` from the repo root.
- When the user opts into iterative commits, commit format is `task(<id>): <imperative summary>`.

---

## Claude Code workflow notes

- Use **TodoWrite** to track sub-steps for any implementation that spans multiple files or phases.
- Use **plan mode** (`/plan` or Shift+Tab) to discuss design before writing code — especially for tasks that touch data contracts or the agent graph.
- Run `./scripts/validate-task.sh` via Bash after every substantive edit.
- Prefer parallel tool calls when reading multiple independent files (e.g., reading `TASKS.md` and `TASK_STATUS.md` simultaneously).
- Do not commit unless the user explicitly requests it.

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
    | "idle"
    | "planning"
    | "generating"
    | "validating"
    | "rendering"
    | "done"
    | "error";
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
- Use Pydantic v2 for all data models. All models live in `backend/study-guide-agent/app/types.py`. Never define ad-hoc dicts for structured data.
- Use `async`/`await` throughout. All Gemini calls are async. All file I/O is async.
- Never use `print()` for debugging — use the `logging` module with appropriate levels.

### ADK agent graph

- The dynamic workflow definition is the single source of truth for execution order. It lives in `backend/study-guide-agent/app/agent.py`.
- The workflow uses ADK 2.0 **dynamic workflows**: `@node` decorator + `ctx.run_node()` + plain Python. Do NOT use graph-based workflow syntax (`edges` array, `JoinNode`, `Event(route=...)`).
- Wave parallelism uses `asyncio.gather()` — not any framework parallel primitive.
- Retry logic for failed sections is a `while` loop calling `ctx.run_node()` with a new retry node instance — not conditional graph edges.
- Every node is a `@node`-decorated function. Nodes receive their inputs as function arguments from `ctx.run_node()` — they do not read from or write to a session state dictionary.
- The `study_guide_workflow` orchestrator node is decorated with `@node(rerun_on_resume=True)` so ADK checkpoints it on resume.

### Gemini calls

- All Gemini calls go through the shared wrapper in `backend/study-guide-agent/app/nodes/base.py`. Never instantiate the Gemini client directly in a node file.
- Always set `response_mime_type="application/json"` for section generation calls.
- Temperature settings per call type:
  - Blueprint: `0.3`
  - Section generation: `0.7`
  - Answer key: `0.3`
  - Retry calls: `0.3`
- Max output tokens: `2048` for all calls unless a section has a documented exception.

### Prompt templates

- All prompt templates live in `backend/study-guide-agent/app/prompts/templates/`. One file per section type.
- Every template file exports a single function: `def build_prompt(spec, blueprint, request) -> str`
- Prompts must include the output JSON schema inline. Never rely on Gemini inferring the schema.
- Never hardcode market, grade, or subject strings inside a template. Always read from `blueprint` or `request`.

### Validators

- Hard validators live in `backend/study-guide-agent/app/validators/hard/`. Soft validators in `backend/study-guide-agent/app/validators/soft/`.
- Validators take explicit structured inputs and return a `ValidationResult`.
- Hard validators raise nothing — they return `ValidationResult(passed=False, ...)`. Never use exceptions for validation logic.
- The retry prompt for a failed section must include the specific failure message from the validator, not a generic retry instruction.

### PDF rendering

- The WeasyPrint renderer lives in `backend/study-guide-agent/app/nodes/renderer.py`.
- The HTML template lives in `backend/study-guide-agent/app/templates/study_guide.html.j2` (Jinja2).
- Section order in the HTML template is the canonical definition of the 17-section order. Never derive section order from anywhere else.
- The answer key section always starts on a new page (`page-break-before: always` in CSS).

---

## Data contracts

The JSON contract between frontend and backend is documented in `ARCHITECTURE.md` section 6.
When changing any field in `backend/study-guide-agent/app/types.py`, the corresponding type in `frontend/lib/types.ts` must be updated in the same commit. These must always be in sync.

Key types:

- `GenerateRequest` — sent from frontend to ADK backend
- `Blueprint` — generated by the blueprint node, passed to dependent section nodes as function arguments
- `GenerateResponse` — returned from ADK backend to frontend on completion
- `ProgressEvent` — streamed via SSE during generation

---

## The 17 fixed sections

The study guide always contains exactly these sections in this order. Never add, remove, or reorder them without updating both `ARCHITECTURE.md` and the HTML renderer template.

| #   | Section key             | Depends on             |
| --- | ----------------------- | ---------------------- |
| 1   | `intro`                 | blueprint              |
| 2   | `learning_targets`      | blueprint              |
| 3   | `warmup`                | blueprint              |
| 4   | `vocabulary`            | blueprint              |
| 5   | `core_explainer`        | blueprint              |
| 6   | `subconcept` ×N         | blueprint              |
| 7   | `strategy_list`         | blueprint              |
| 8   | `deep_dive`             | blueprint              |
| 9   | `model_passage`         | blueprint              |
| 10  | `check_in`              | `model_passage`        |
| 11  | `key_points`            | blueprint              |
| 12  | `assessment_passage`    | blueprint              |
| 13  | `assessment_questions`  | `assessment_passage`   |
| 14  | `step_up`               | `assessment_questions` |
| 15  | `self_assessment`       | blueprint              |
| 16  | `answer_key`            | all question sections  |
| 17  | _(rendered separately)_ | answer key             |

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
ADK_BACKEND_URL=http://localhost:8000
```

### Backend (`backend/study-guide-agent/.env`)

```
GOOGLE_API_KEY=your_key_here
MARKET_DEFAULT=PH
```

---

## Path disambiguation note

This repo lives inside `Documents - Joshua's MacBook Pro/` where the apostrophe is **Unicode U+2019** (RIGHT SINGLE QUOTATION MARK). There is a second similarly-named folder in the same `Documents/` directory that uses an ASCII U+0027 apostrophe — that folder is an iCloud artifact and does NOT contain the repo.

**Shell scripts and Python code must never use `glob` patterns with `iterdir()` to locate this repo**, because iteration order is non-deterministic and may return the wrong directory first. Always anchor on the git directory:

```bash
# Bash — always use this pattern
GITDIR=$(ls -d ~/Documents/Documents*/Study-guide-generation/.git 2>/dev/null | head -1)
WORKTREE="${GITDIR%/.git}"
```

```python
# Python — always pass the path as a CLI argument, not via iterdir()
# Or use: pathlib.Path(os.environ["STUDY_GUIDE_REPO"])
```

The env var `STUDY_GUIDE_REPO` is set in `~/.zshrc` pointing to the correct Unicode-apostrophe path, and can be used as the canonical reference.

## Running locally

```bash
# Backend
cd backend/study-guide-agent
agents-cli install
cp .env.example .env   # then add your API key
uv run uvicorn app.fast_api_app:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev   # starts Next.js on localhost:3000
```
