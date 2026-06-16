# Task Breakdown

## Study Guide Generation Web App

> A detailed, scaffold-aware implementation guide for this repository.
> This version keeps the step-by-step prompts and task instructions from the original plan, but updates all backend assumptions to the current `agents-cli` scaffolded structure.
>
> Use this together with `TASK_STATUS.md`:
>
> - `TASKS.md` is the stable implementation guide.
> - `TASK_STATUS.md` is the live repo snapshot that should be updated as tasks are completed.

---

## How to read this document

**Who does it:**

- 🧑 **You** — terminal commands, scaffolding, file placement, environment setup, test runs, and QA decisions
- 🤖 **Copilot** — code generation and targeted edits in VS Code

**How to use Copilot Chat for each task:**

- Open Copilot Chat with `Cmd+Shift+I`
- Use `@workspace` when the prompt asks Copilot to consider full repo context
- Before accepting edits, ensure Copilot has read `IFC.md`, `ARCHITECTURE.md`, `.github/copilot-instructions.md`, `TASKS.md`, and `TASK_STATUS.md`
- Review generated code before accepting it
- After a task is truly complete, update `TASK_STATUS.md`

**Backend root:**

- The canonical backend project root is `backend/study-guide-agent/`
- All backend application code lives under `backend/study-guide-agent/app/`
- All backend tests live under `backend/study-guide-agent/tests/`
- Do not implement new backend work against the deleted legacy root-level backend layout

**Workflow rule:**

- The backend uses ADK 2.0 dynamic workflows only: `@node`, `ctx.run_node()`, `asyncio.gather()`, and plain Python
- Do not design new tasks around a session state dictionary
- Do not use graph-style `edges`, `JoinNode`, `Event(route=...)`, `SequentialNode`, `LoopNode`, or `ParallelNode`

---

## Repository structure to target

```text
/
├── frontend/
│   ├── app/
│   ├── lib/
│   └── package.json
└── backend/
    └── study-guide-agent/
        ├── app/
        │   ├── agent.py
        │   ├── fast_api_app.py
        │   ├── types.py
        │   ├── nodes/
        │   ├── prompts/
        │   ├── validators/
        │   └── templates/
        ├── tests/
        │   ├── eval/evalsets/
        │   ├── fixtures/legacy_evals/
        │   ├── integration/
        │   └── unit/
        ├── .env.example
        ├── AGENTS.md
        ├── pyproject.toml
        └── uv.lock
```

---

## Phase overview

```text
Phase 0  — Repository and tooling setup
Phase 1  — Backend scaffold alignment
Phase 2  — Data contracts and type sync
Phase 3  — System prompt and blueprint generation
Phase 4  — Section generation nodes
Phase 5  — Validation layer
Phase 6  — Renderer and preview payload
Phase 7  — Workflow orchestration
Phase 8  — Frontend shell and cleanup
Phase 9  — Teacher input form
Phase 10 — API proxy and streaming progress
Phase 11 — Results experience
Phase 12 — End-to-end validation and QA
Phase 13 — Deployment and parity
Phase 14 — Prompt Lab MVP
Phase 18 — Subject-agnostic deep dive
Phase 19 — Soft validator quality improvements
```

Deployment checkpoints should be exercised before the end of the roadmap:

- After Phase 7 is working well enough to boot the real backend workflow, validate a backend-only remote deployment.
- After Phase 10 is working, validate the deployed proxy and SSE path in the remote staging environment.
- After Phase 12 passes, run a full release-candidate deployment and smoke test.

---

## Phase 0 — Repository and tooling setup

> Goal: reach a clean local setup where both runtimes exist, the scaffolded backend is the canonical target, and the repo documents reflect that structure before implementation work begins.

---

### Task 0.1 — Confirm repository baseline

🧑 **You**

Verify these root documents exist:

```text
IFC.md
ARCHITECTURE.md
README.md
TASKS.md
TASK_STATUS.md
.github/copilot-instructions.md
```

Verify the workspace structure contains:

```text
frontend/
backend/study-guide-agent/
```

**Done looks like:**

- Root docs are present
- The scaffolded backend exists
- `TASK_STATUS.md` reflects the current repo accurately

---

### Task 0.2 — Verify the scaffolded backend project

🧑 **You**

Run from the scaffold root:

```bash
cd backend/study-guide-agent
export PATH="/Users/joshuawenghao/.local/bin:$PATH"
agents-cli info
```

Expected outcome:

- `agents-cli` recognizes `backend/study-guide-agent/` as a valid project

If `agents-cli` is not on `PATH`, continue using the export above or the absolute path:

```bash
/Users/joshuawenghao/.local/bin/agents-cli info
```

**Done looks like:**

- `agents-cli info` succeeds in `backend/study-guide-agent/`

---

### Task 0.3 — Install backend dependencies and create environment files

🧑 **You**

Run:

```bash
cd backend/study-guide-agent
export PATH="/Users/joshuawenghao/.local/bin:$PATH"
agents-cli install
```

If the local environment file is missing, create it from the scaffold example:

```bash
cp .env.example .env
```

The backend environment file should contain at least:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
MARKET_DEFAULT=PH
```

Do not commit `.env`.

**Done looks like:**

- `agents-cli install` succeeds
- `backend/study-guide-agent/.env.example` exists
- `backend/study-guide-agent/.env` exists locally

---

### Task 0.4 — Verify the frontend runtime

🧑 **You**

From `frontend/`:

```bash
cd frontend
npm install
npm run dev
```

Create `frontend/.env.local` if it does not exist:

```env
ADK_BACKEND_URL=http://localhost:8000
```

Create or verify `frontend/.env.local.example` contains the same value.

**Done looks like:**

- `npm run dev` starts Next.js successfully
- `frontend/.env.local` exists locally

---

### Task 0.5 — Verify evaluation assets and fixture roles

🧑 **You**

Check that both evaluation layers exist:

```text
backend/study-guide-agent/tests/eval/evalsets/
backend/study-guide-agent/tests/fixtures/legacy_evals/
```

Keep this distinction clear:

- `tests/eval/evalsets/` = scaffold-native `agents-cli` evalsets
- `tests/fixtures/legacy_evals/` = preserved structured acceptance fixtures from the previous backend layout

**Done looks like:**

- Both folders exist
- The distinction is documented in the scaffold README

---

**✅ Phase 0 done.** The repo is ready for product implementation inside the scaffolded backend and the existing frontend.

---

## Phase 1 — Backend scaffold alignment

> Goal: make the scaffolded backend the full target structure for the study-guide app and remove any remaining sample-agent assumptions.

---

### Task 1.1 — Confirm the backend file tree exists in the scaffold

🧑 **You**

Verify these paths exist under `backend/study-guide-agent/app/`:

```text
app/agent.py
app/fast_api_app.py
app/types.py
app/nodes/base.py
app/nodes/blueprint.py
app/nodes/validator.py
app/nodes/renderer.py
app/nodes/sections/
app/prompts/system_prompt.py
app/prompts/templates/
app/validators/hard/
app/validators/soft/
app/templates/study_guide.html.j2
```

Also verify tests directories exist:

```text
tests/unit/
tests/integration/
tests/eval/evalsets/
tests/fixtures/legacy_evals/
```

**Done looks like:**

- The full scaffold tree for the study-guide implementation surface exists

---

### Task 1.2 — Align the scaffold’s shared Gemini wrapper

🤖 **Copilot**

Open `backend/study-guide-agent/app/nodes/base.py`. Open Copilot Chat and paste:

```text
@workspace
Implement or verify backend/study-guide-agent/app/nodes/base.py for the study-guide workflow.

This file must provide shared Gemini utilities for ADK 2.0 dynamic workflows.

Requirements:
1. Temperature constants:
   TEMP_BLUEPRINT = 0.3
   TEMP_SECTION = 0.7
   TEMP_ANSWER_KEY = 0.3
   TEMP_RETRY = 0.3

2. MAX_OUTPUT_TOKENS = 2048

3. MODEL_NAME = "gemini-3.5-flash"

4. async def call_gemini(system_prompt, user_prompt, temperature, max_retries=2, context_label="unknown") -> str
   - Calls Gemini with response_mime_type="application/json"
   - Retries failed calls with a 1 second delay
   - Returns the raw response text
   - Raises RuntimeError after all retries fail

Constraints:
- Do not add any session state helper functions
- Do not instantiate Gemini clients inside section nodes
- Use logging instead of print()
```

**Done looks like:**

- `app/nodes/base.py` is a reusable shared Gemini wrapper for all later nodes

---

### Task 1.3 — Align the scaffold entrypoint with the study-guide app identity

🤖 **Copilot**

Open `backend/study-guide-agent/app/agent.py`. Open Copilot Chat and paste:

```text
@workspace
Update backend/study-guide-agent/app/agent.py so it is no longer the sample scaffold agent.

For now, keep it as a minimal study-guide-specific bootstrap until the full dynamic workflow is implemented.

Requirements:
- Use model="gemini-3.5-flash"
- Agent name should be study-guide specific
- Description should mention structured K-12 study guide generation
- Instruction should mention the fixed 17-section format and asking for missing curriculum details instead of inventing them
- Keep the file simple for now; the full workflow wiring comes in Phase 7
- Export app = App(root_agent=..., name="study-guide-agent")
```

Open `backend/study-guide-agent/app/fast_api_app.py`. Open Copilot Chat and paste:

```text
@workspace
Update backend/study-guide-agent/app/fast_api_app.py to be a simple local FastAPI entrypoint for the study-guide agent.

Requirements:
- Use get_fast_api_app from google.adk.cli.fast_api
- Point agents_dir at the scaffold app root
- Disable sample-project-specific cloud assumptions unless they are required
- Keep title and description aligned with the study-guide app
- Keep the file compatible with local development via uvicorn
```

**Done looks like:**

- The scaffold no longer presents itself as a generic sample agent
- The scaffold can serve as the real study-guide backend target

---

**✅ Phase 1 done.** The scaffold is aligned to the study-guide project and ready for actual product logic.

---

## Phase 2 — Data contracts and type sync

> Goal: define the backend data contract once and mirror it in the frontend so every later task shares the same shapes.

---

### Task 2.1 — Implement backend data contracts

🤖 **Copilot**

Open `backend/study-guide-agent/app/types.py`. Open Copilot Chat and paste:

```text
@workspace
Implement backend/study-guide-agent/app/types.py in full.

Use Pydantic v2 and read ARCHITECTURE.md section 6 before writing code.

Include all of the following:
- LengthPreset enum
- TopicDomains
- SubCompetency
- LessonMetadata
- Curriculum
- InstructionalDesign
- OptionalInputs
- GenerateRequest
- LearningTarget
- VocabEntry
- Blueprint
- PreviewSection
- WebPreviewPayload
- ValidationResult
- GenerateResponse
- ProgressEventType literal union
- ProgressEvent

Requirements:
- Use Field() descriptions on complex fields
- Keep this file as the source of truth for the backend/frontend contract
- Add a module docstring explaining that this file defines the study-guide data contract
```

**Done looks like:**

- `backend/study-guide-agent/app/types.py` fully matches the documented backend contract

---

### Task 2.2 — Mirror the contract in the frontend

🤖 **Copilot**

Open `frontend/lib/types.ts`. Open Copilot Chat and paste:

```text
@workspace
Implement frontend/lib/types.ts so it mirrors backend/study-guide-agent/app/types.py exactly.

Convert Python types to strict TypeScript equivalents.
Include all shared request, blueprint, preview, validation, response, and progress types.
Also include:
- GenerationStage = 'idle' | 'planning' | 'generating' | 'validating' | 'rendering' | 'done' | 'error'

Constraints:
- No any
- No inline types in component files later
- Add a file header comment noting that it mirrors backend/study-guide-agent/app/types.py and must be updated in the same commit when fields change
```

**Done looks like:**

- `frontend/lib/types.ts` matches the backend contract semantically and structurally

---

### Task 2.3 — Verify sync manually

🧑 **You**

Open both files side by side and verify:

- Every backend field exists in the frontend equivalent
- Literal unions and enums are represented clearly
- Optional fields still mean the same thing across both runtimes

Commit after both files are in sync.

**Done looks like:**

- No contract drift exists between backend and frontend

---

### Task 2.4 — Extend the preview contract for iconography

🤖 **Copilot**

Open `backend/study-guide-agent/app/types.py` and `frontend/lib/types.ts`. Open Copilot Chat and paste:

```text
@workspace
Extend the shared study-guide preview contract for renderer-owned iconography.

Read ARCHITECTURE.md sections 6, 8, and 9 before editing.

Requirements:
- Add optional icon metadata for preview sections without changing the request contract
- Keep icons presentation-only; they must not become required instructional content
- Mirror the backend and frontend contract changes in the same edit slice
- Preserve strict typing on both sides

Constraints:
- Do not add teacher-configurable icon inputs
- Do not add generated image payloads or asset upload fields
- Keep backwards compatibility by making new icon fields optional
```

**Done looks like:**

- Backend and frontend preview contracts can carry optional icon metadata with no request-shape changes

---

**Phase 2 note.** Shared types are in place for the shipped prototype, and Task 2.4 extends that contract for the planned iconography slice.

---

## Phase 3 — System prompt and blueprint generation

> Goal: implement the first real generation path. The blueprint is the shared structured context that all later sections depend on.

---

### Task 3.1 — Implement the system prompt builder

🤖 **Copilot**

Open `backend/study-guide-agent/app/prompts/system_prompt.py`. Open Copilot Chat and paste:

```text
@workspace
Implement backend/study-guide-agent/app/prompts/system_prompt.py in full.

Export one function:
    def build_system_prompt(request: GenerateRequest) -> str

The prompt must include:
- Role statement for the market, grade level, and subject
- Reading level guidance aligned to the requested grade
- Voice rules: warm, clear, encouraging, never condescending
- Formatting rules: valid JSON only, no markdown code fences, no prose outside JSON
- Cultural relevance rule using the request market
- Output discipline rule for structured generation

Constraints:
- Import GenerateRequest from app.types
- Use plain Python string building only
- Do not use Jinja2 here
```

**Done looks like:**

- The global system prompt builder is implemented and request-aware

---

### Task 3.2 — Implement the blueprint prompt template

🤖 **Copilot**

Create `backend/study-guide-agent/app/prompts/templates/blueprint.py` if it does not exist.
Then open it and paste:

```text
@workspace
Implement backend/study-guide-agent/app/prompts/templates/blueprint.py in full.

Export one function:
    def build_prompt(spec, blueprint, request) -> str

For this file, `request` is the actual required input and `spec`/`blueprint` can remain unused to preserve prompt-template consistency across the project.

The blueprint prompt must:
- Reflect lesson title, grade level, subject, market, and competency code
- Build a full essential question from essential_question_seed
- Generate exactly 5 vocabulary entries unless teacher-provided seeds change that behavior later
- Require DIFFERENT topic domains for model_passage and assessment_passage
- Produce student-facing learning targets derived from bloom targets
- Include the expected Blueprint schema inline
- End with a strict "return only JSON" instruction
```

**Done looks like:**

- The blueprint prompt returns the documented schema and enforces passage domain separation

---

### Task 3.3 — Implement the blueprint node

🤖 **Copilot**

Open `backend/study-guide-agent/app/nodes/blueprint.py`. Open Copilot Chat and paste:

```text
@workspace
Implement backend/study-guide-agent/app/nodes/blueprint.py in full using ADK 2.0 dynamic workflow conventions.

Requirements:
- The node should accept GenerateRequest as a direct input argument
- Build the system prompt from app.prompts.system_prompt
- Build the blueprint user prompt from app.prompts.templates.blueprint
- Call call_gemini() with TEMP_BLUEPRINT
- Parse the response as JSON
- Validate it as a Blueprint Pydantic model
- Return the validated Blueprint object
- Raise RuntimeError with raw response context on parse failure

Constraints:
- Do not read from or write to a session state dictionary
- Use explicit arguments and return values only
```

**Done looks like:**

- The blueprint node is the first real backend generation node and returns a validated Blueprint

---

### Task 3.4 — Add a focused blueprint test

🧑 **You**

Create a dedicated test file under `backend/study-guide-agent/tests/`.
A good location is:

```text
backend/study-guide-agent/tests/unit/test_blueprint.py
```

🤖 **Copilot**

Open the new file and paste:

```text
@workspace
Write a focused pytest test for the blueprint node.

Requirements:
- Build a realistic GenerateRequest using the English Grade 6 PH fixture values
- Call the blueprint node directly
- Assert the returned object has all required Blueprint fields
- Assert learning_targets has the expected count
- Assert model_passage and assessment_passage domains differ

Constraints:
- Mark async tests with pytest.mark.asyncio
- Keep the test focused on the blueprint path only
```

Run the focused test after implementation.

**Done looks like:**

- A narrow executable test can falsify the blueprint path independently of the rest of the app

---

**✅ Phase 3 done.** The backend can generate and validate the shared blueprint context.

---

## Phase 4 — Section generation nodes

> Goal: implement all section prompt templates and nodes in dependency order. Build prompts first, then nodes, then focused tests.

---

### Task 4.1 — Implement Wave 1 section prompt templates

🤖 **Copilot**

These depend only on the blueprint.
Implement these files one at a time under `backend/study-guide-agent/app/prompts/templates/`:

- `intro.py`
- `learning_targets.py`
- `warmup.py`
- `vocabulary.py`
- `key_points.py`
- `self_assessment.py`

For each file, open it and use a prompt like this, replacing the section-specific schema:

```text
@workspace
Implement backend/study-guide-agent/app/prompts/templates/intro.py in full.

Export:
    def build_prompt(spec, blueprint, request) -> str

Use `blueprint` as the main input.
The prompt must:
- Explain the exact JSON shape expected for the section
- Use the blueprint fields directly
- Include the output schema inline
- End with a strict instruction to return JSON only

Do not use placeholders like TODO or pass.
```

Section-specific guidance:

- `intro`: warm opening linked to the essential question and introduction hook
- `learning_targets`: competency + student-facing “I can” statements aligned to blueprint targets
- `warmup`: short activation activity with purpose statement
- `vocabulary`: one structured entry per blueprint vocabulary word
- `key_points`: numbered summary statements aligned to sub-competencies
- `self_assessment`: rows whose `skill` fields match learning target objectives verbatim

**Done looks like:**

- All Wave 1 templates are implemented and schema-specific

---

### Task 4.2 — Implement Wave 1 section nodes

🤖 **Copilot**

Implement these node files under `backend/study-guide-agent/app/nodes/sections/`:

- `intro.py`
- `learning_targets.py`
- `warmup.py`
- `vocabulary.py`
- `key_points.py`
- `self_assessment.py`

Use this prompt pattern for each:

```text
@workspace
Implement backend/study-guide-agent/app/nodes/sections/intro.py using ADK 2.0 dynamic workflow conventions.

Requirements:
- Accept explicit inputs needed by the node
- Build the system prompt from the original GenerateRequest
- Build the section prompt from the matching prompt template
- Call call_gemini() with TEMP_SECTION
- Parse JSON and return the structured section payload
- Raise RuntimeError on malformed JSON

Constraints:
- Do not read from or write to a session state dictionary
- Do not instantiate the Gemini client here
```

Practical input rule:

- Pass both `request` and `blueprint` into nodes that need the system prompt plus section context

**Done looks like:**

- All Wave 1 nodes return parsed structured outputs using explicit inputs only

---

### Task 4.3 — Implement Wave 2 templates and nodes

🤖 **Copilot**

Implement the prompt templates and nodes for:

- `core_explainer`
- `subconcept`
- `strategy_list`
- `deep_dive`
- `model_passage`
- `assessment_passage`

Guidance:

- `subconcept` should support one call per sub-competency
- `model_passage` and `assessment_passage` must use different domains from the blueprint
- `assessment_passage` should be written with downstream answerability in mind

Template prompt pattern:

```text
@workspace
Implement backend/study-guide-agent/app/prompts/templates/model_passage.py in full.

Requirements:
- Export build_prompt(spec, blueprint, request)
- Use the blueprint topic domain assigned to model_passage
- Define the exact JSON schema inline
- Require evidence-friendly passage writing suitable for downstream questions and validators
```

Node prompt pattern:

```text
@workspace
Implement backend/study-guide-agent/app/nodes/sections/model_passage.py in full.

Requirements:
- Accept explicit inputs
- Build prompts using request + blueprint
- Call call_gemini() with TEMP_SECTION
- Parse and return structured JSON
```

**Done looks like:**

- Wave 2 sections exist and can be generated from explicit inputs only

---

### Task 4.4 — Implement Wave 3 templates and nodes

🤖 **Copilot**

Implement:

- `check_in`
- `assessment_questions`
- `step_up`

These depend on earlier sections and must take those dependencies directly as arguments.

Prompt template guidance:

- `check_in` uses `model_passage`
- `assessment_questions` uses `assessment_passage`
- `step_up` uses `assessment_questions` and can also use `assessment_passage`

Use this prompt pattern:

```text
@workspace
Implement backend/study-guide-agent/app/prompts/templates/check_in.py in full.

Requirements:
- Export build_prompt(spec, blueprint, request)
- The prompt must be able to consume the upstream dependent section payload through `spec` or an equivalent structured input
- Include the exact output JSON schema inline
- Write questions that require evidence from the provided passage text
```

Use this node pattern:

```text
@workspace
Implement backend/study-guide-agent/app/nodes/sections/check_in.py in full.

Requirements:
- Accept explicit inputs including the dependent upstream section payload
- Build system and section prompts
- Call call_gemini() with TEMP_SECTION
- Parse and return structured JSON

Constraints:
- No session state reads or writes
```

**Done looks like:**

- Wave 3 generation consumes direct dependency inputs instead of a shared state dict

---

### Task 4.5 — Implement the answer key template and node

🤖 **Copilot**

Implement:

- `backend/study-guide-agent/app/prompts/templates/answer_key.py`
- `backend/study-guide-agent/app/nodes/sections/answer_key.py`

Open the template file and paste:

```text
@workspace
Implement backend/study-guide-agent/app/prompts/templates/answer_key.py in full.

Requirements:
- Export build_prompt(spec, blueprint, request)
- The prompt must consume check_in, assessment_passage, and assessment_questions outputs as structured inputs
- Require every possible_answer for assessment questions to include at least one verbatim quoted phrase from assessment_passage
- Include the exact JSON schema inline
- End with a strict JSON-only instruction
```

Open the node file and paste:

```text
@workspace
Implement backend/study-guide-agent/app/nodes/sections/answer_key.py in full.

Requirements:
- Accept explicit dependencies: request, blueprint, check_in, assessment_passage, assessment_questions
- Build prompts
- Call call_gemini() with TEMP_ANSWER_KEY
- Parse and return structured JSON
- Preserve quoted-evidence requirements for downstream hard validators
```

**Done looks like:**

- The answer key path is implemented and structurally ready for quoted-evidence validation

---

### Task 4.6 — Add focused section-generation tests

🧑 **You**

Create a dedicated section-generation test module under `backend/study-guide-agent/tests/`.

🤖 **Copilot**

Open the new file and paste:

```text
@workspace
Write focused pytest tests for section generation.

Requirements:
- Use a hardcoded or fixture-based Blueprint input
- Add narrow tests for a few representative Wave 1 sections
- Add at least one dependency-aware test for Wave 3 sections
- Add a shape-focused test for answer_key output

Constraints:
- Keep tests focused
- Use pytest.mark.asyncio for async node tests
- Do not test the whole workflow here
```

**Done looks like:**

- Section-generation tests exist and validate shape and dependency flow without requiring the full app to run

---

**✅ Phase 4 done.** All section-generation paths are implemented in dependency order.

---

## Phase 5 — Validation layer

> Goal: implement all hard and soft validators with explicit structured inputs, then aggregate them in the validator node.

---

### Task 5.1 — Implement hard validator: json_schema

🤖 **Copilot**

Open `backend/study-guide-agent/app/validators/hard/json_schema.py`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/validators/hard/json_schema.py in full.

Requirements:
- Validate that section outputs parse against their expected structured schema or model shape
- Return a ValidationResult
- Never raise for validation failure; return passed=False with failure messages instead
- Keep the interface explicit and compatible with the validator aggregation node
```

---

### Task 5.2 — Implement hard validator: vocab_presence

🤖 **Copilot**

Open `backend/study-guide-agent/app/validators/hard/vocab_presence.py`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/validators/hard/vocab_presence.py in full.

Requirements:
- Accept explicit structured inputs
- Check that every blueprint vocabulary word appears in the combined body-section text, case-insensitively
- Exclude the vocabulary section itself and the answer key from the body-text search
- Return ValidationResult with meaningful failure messages
```

---

### Task 5.3 — Implement hard validator: self_assess_targets

🤖 **Copilot**

Open `backend/study-guide-agent/app/validators/hard/self_assess_targets.py`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/validators/hard/self_assess_targets.py in full.

Requirements:
- Accept explicit inputs for blueprint and self_assessment output
- Verify each self-assessment skill matches a learning target objective verbatim
- Return ValidationResult
```

---

### Task 5.4 — Implement hard validator: answer_key_quotes

🤖 **Copilot**

Open `backend/study-guide-agent/app/validators/hard/answer_key_quotes.py`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/validators/hard/answer_key_quotes.py in full.

Requirements:
- Accept explicit inputs for answer_key and assessment_passage
- Verify each answer contains at least one quoted phrase
- Verify quoted phrases appear verbatim in the assessment passage body
- Return ValidationResult with clear question-level failure details
```

---

### Task 5.5 — Implement hard validator: passage_domain_diff

🤖 **Copilot**

Open `backend/study-guide-agent/app/validators/hard/passage_domain_diff.py`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/validators/hard/passage_domain_diff.py in full.

Requirements:
- Accept blueprint as input
- Compare model_passage and assessment_passage topic domains case-insensitively
- Return passed=False if they are equal or missing
```

---

### Task 5.6 — Implement soft validator: answer_leakage

🤖 **Copilot**

Open `backend/study-guide-agent/app/validators/soft/answer_leakage.py`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/validators/soft/answer_leakage.py in full.

Requirements:
- Accept explicit structured inputs
- Detect answer leakage into body sections using quoted evidence phrases
- Always return passed=True
- Populate warnings when leakage is found
```

---

### Task 5.7 — Implement soft validator: reading_level

🤖 **Copilot**

Open `backend/study-guide-agent/app/validators/soft/reading_level.py`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/validators/soft/reading_level.py in full.

Requirements:
- Accept grade expectation plus section content inputs
- Use textstat or another appropriate reading-level computation approach
- Warn when a section is materially outside the expected grade band
- Always return passed=True and use warnings only
```

Add `textstat` to the backend project dependencies if needed.

---

### Task 5.8 — Implement the validator node

🤖 **Copilot**

Open `backend/study-guide-agent/app/nodes/validator.py`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/nodes/validator.py using ADK 2.0 dynamic workflow conventions.

Requirements:
- Accept explicit structured inputs for blueprint and all generated sections
- Run all hard validators
- Run all soft validators
- Aggregate the outputs into one ValidationResult
- Return the ValidationResult directly

Constraints:
- No session state reads or writes
- No exceptions for normal validation failures
```

---

### Task 5.9 — Add validator tests

🧑 **You**

Create a focused validator test file under `backend/study-guide-agent/tests/`.

🤖 **Copilot**

Open it and paste:

```text
@workspace
Write focused pytest tests for the study-guide validators.

Requirements:
- Add a failing and passing case for vocab_presence
- Add a failing case for self_assess_targets
- Add a failing and passing case for answer_key_quotes
- Add a failing case for passage_domain_diff
- Add a warning-only case for answer_leakage

Constraints:
- Use hardcoded structured fixtures
- Do not call Gemini
```

**Done looks like:**

- The validator layer is executable and falsifiable in isolation

---

**✅ Phase 5 done.** The backend can now judge generated outputs against project constraints before rendering.

---

## Phase 6 — Renderer and preview payload

> Goal: produce both the PDF and the structured preview payload from validated outputs.

---

### Task 6.1 — Implement the study guide HTML template

🤖 **Copilot**

Open `backend/study-guide-agent/app/templates/study_guide.html.j2`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/templates/study_guide.html.j2 in full.

Requirements:
- Encode the canonical 17-section order documented in ARCHITECTURE.md
- Use Jinja2 syntax only
- Be suitable for WeasyPrint
- Start the assessment passage on a new page
- Start the answer key on a new page
- Use readable headings, tables, callouts, and section grouping appropriate for a study guide
```

**Done looks like:**

- The Jinja template defines the canonical PDF section order and layout

---

### Task 6.2 — Implement the renderer node

🤖 **Copilot**

Open `backend/study-guide-agent/app/nodes/renderer.py`. Paste:

```text
@workspace
Implement backend/study-guide-agent/app/nodes/renderer.py in full.

Requirements:
- Accept blueprint, generated sections, and validation result as explicit inputs
- Load the Jinja2 template from app/templates/study_guide.html.j2
- Render HTML and convert it to a PDF with WeasyPrint
- Base64-encode the PDF bytes
- Build a WebPreviewPayload in canonical section order
- Return the final rendered artifacts in a structured result compatible with GenerateResponse

Constraints:
- No session state reads or writes
- Keep section order canonical and explicit
```

**Done looks like:**

- The renderer produces both PDF output and preview JSON from explicit inputs

---

### Task 6.3 — Add renderer tests

🧑 **You**

Create a focused renderer test file under `backend/study-guide-agent/tests/`.

🤖 **Copilot**

Open it and paste:

```text
@workspace
Write focused pytest tests for the renderer.

Requirements:
- Build a minimal but valid set of blueprint and section payloads
- Call the renderer directly
- Assert that the PDF output decodes to bytes starting with the PDF header
- Assert that the preview sections appear in canonical order
```

**Done looks like:**

- The renderer has a focused executable check independent of the full workflow

---

### Task 6.4 — Add deterministic iconography to the renderer and PDF template

🤖 **Copilot**

Open `backend/study-guide-agent/app/nodes/renderer.py` and `backend/study-guide-agent/app/templates/study_guide.html.j2`. Paste:

```text
@workspace
Implement the first-pass iconography system for the study-guide renderer and PDF template.

Read ARCHITECTURE.md section 8 before editing.

Requirements:
- Keep icon selection deterministic and renderer-owned
- Emit optional icon metadata in the preview payload based on section type and supported UI roles
- Add icon treatments to the WeasyPrint-safe Jinja template for section headers and selected repeated callouts
- Use inline SVG or equivalent template-owned markup that survives PDF rendering reliably
- Fall back to text-only rendering if an icon key is unknown or unsupported

Constraints:
- Do not call Gemini for icon selection
- Do not add generated images, uploaded assets, or remote image dependencies
- Keep the canonical section order unchanged
```

**Done looks like:**

- The backend renderer and PDF template apply the new iconography system without changing guide content semantics

---

### Task 6.5 — Add focused renderer iconography tests

🧑 **You**

Run the narrowest validation available after the first iconography renderer implementation.
Examples:

```bash
cd backend/study-guide-agent
uv run pytest tests/unit/test_renderer.py -q
```

If needed, extend the focused renderer tests first so they assert both preview `icon_key` emission and a stable PDF render path when icon markup is present.

**Done looks like:**

- Focused renderer tests cover icon metadata and confirm the PDF render path still succeeds

---

**Phase 6 note.** Rendering is in place for the shipped prototype, and Tasks 6.4 through 6.5 extend that renderer for the planned iconography slice.

---

## Phase 7 — Workflow orchestration

> Goal: wire the full dynamic workflow in `app/agent.py` using explicit inputs, wave parallelism, validator retry, and rendering.

---

### Task 7.1 — Implement the orchestrator workflow

🤖 **Copilot**

Open `backend/study-guide-agent/app/agent.py`. Paste:

```text
@workspace
Implement the study-guide workflow in backend/study-guide-agent/app/agent.py using ADK 2.0 dynamic workflows.

Read ARCHITECTURE.md section 4 before writing code.

Requirements:
- Use @node and ctx.run_node() only
- Use asyncio.gather() for wave parallelism
- Accept GenerateRequest as the workflow input
- Generate blueprint first
- Run Wave 1 sections in parallel
- Run Wave 2 sections in parallel
- Run Wave 3 sections using explicit dependencies
- Run answer_key last
- Run validator after generation
- Retry only failed sections using explicit retry prompts and lower retry temperature
- Run renderer last
- Return the final rendered result

Constraints:
- Do not use graph edges, JoinNode, or session-state dicts
- Keep retry logic in plain Python using a while loop
```

**Done looks like:**

- `app/agent.py` becomes the real dynamic workflow entrypoint, not just a sample bootstrap

---

### Task 7.2 — Add a focused backend-only integration check

🧑 **You**

Run the narrowest validation available after the first workflow implementation.
Examples:

```bash
cd backend/study-guide-agent
uv run pytest tests/unit tests/integration -q
```

If full tests are too broad initially, add a narrower backend integration case first.

**Done looks like:**

- The workflow can be validated through at least one focused executable path

---

**✅ Phase 7 done.** The backend now owns the full generation pipeline.

---

## Phase 8 — Frontend shell and cleanup

> Goal: convert the default Next.js scaffold into the app shell for the study-guide UI.

---

### Task 8.1 — Remove default Next.js boilerplate

🧑 **You**

Clean up the frontend scaffold so it is ready for the study-guide UI.

Typical work:

- Remove the default demo content in `frontend/app/page.tsx`
- Simplify `frontend/app/globals.css` if it still reflects starter styles
- Create `frontend/components/` if it does not yet exist

**Done looks like:**

- The default Next.js landing page is gone
- The project is ready for real app UI work

---

### Task 8.2 — Implement global styles and app layout

🤖 **Copilot**

Open `frontend/app/globals.css` and `frontend/app/layout.tsx`. Paste:

```text
@workspace
Implement the frontend shell for the study-guide app.

Requirements:
- globals.css should keep custom CSS minimal and rely primarily on Tailwind
- layout.tsx should define the app title and a clean, education-oriented shell
- The visual direction should fit a teacher-facing productivity tool, not the default starter page
```

**Done looks like:**

- The frontend shell feels like the intended product, not the create-next-app template

---

### Task 8.3 — Create empty component stubs

🧑 **You**

Create these component files if they do not exist yet:

```text
frontend/components/InputForm.tsx
frontend/components/ProgressTracker.tsx
frontend/components/WebPreview.tsx
frontend/components/DownloadButton.tsx
frontend/components/PreviewSection.tsx
```

**Done looks like:**

- The component structure exists for later phases

---

**✅ Phase 8 done.** The frontend shell is ready for the teacher form and results UI.

---

## Phase 9 — Teacher input form

> Goal: build the controlled form that creates a valid `GenerateRequest`.

---

### Task 9.1 — Implement InputForm.tsx

🤖 **Copilot**

Open `frontend/components/InputForm.tsx`. Paste:

```text
@workspace
Implement frontend/components/InputForm.tsx in full.

Requirements:
- Fully controlled component
- Uses GenerateRequest from frontend/lib/types.ts
- Includes grouped sections for lesson details, curriculum, instructional design, and optional inputs
- Supports dynamic sub-competency rows
- Prevents default form submission behavior
- Validates required fields before calling onSubmit
- Props:
  { onSubmit: (request: GenerateRequest) => void, isLoading: boolean }
```

**Done looks like:**

- Teachers can enter all required structured study-guide inputs

---

### Task 9.2 — Update page.tsx for form state

🤖 **Copilot**

Open `frontend/app/page.tsx`. Paste:

```text
@workspace
Implement frontend/app/page.tsx for the form stage.

Requirements:
- Manage GenerationStage state
- Render InputForm in the idle state
- Hold basic page-level error state
- Prepare the page for API integration later without implementing streaming yet
```

**Done looks like:**

- The form renders and page state is ready for backend submission

---

**✅ Phase 9 done.** The teacher-facing input flow is in place.

---

## Phase 10 — API proxy and streaming progress

> Goal: proxy backend generation through the Next.js API route and stream progress events to the browser.

---

### Task 10.1 — Implement the generate route

🤖 **Copilot**

Open or create `frontend/app/api/generate/route.ts`. Paste:

```text
@workspace
Implement frontend/app/api/generate/route.ts in full.

Requirements:
- Parse GenerateRequest
- Forward it to the backend URL from ADK_BACKEND_URL
- Re-stream backend progress events as SSE to the browser
- Keep the route thin
- Use native fetch and stream primitives only
```

**Done looks like:**

- The frontend can submit requests to the backend through its own route layer

---

### Task 10.2 — Implement ProgressTracker.tsx

🤖 **Copilot**

Open `frontend/components/ProgressTracker.tsx`. Paste:

```text
@workspace
Implement frontend/components/ProgressTracker.tsx in full.

Requirements:
- Accept generation stage, events, and elapsed time
- Render a step-based progress view
- Reflect blueprint, generation, validation, retry, render, and done states clearly
```

**Done looks like:**

- The frontend has a dedicated progress component for streamed generation events

---

### Task 10.3 — Wire streaming into page.tsx

🤖 **Copilot**

Open `frontend/app/page.tsx`. Paste:

```text
@workspace
Update frontend/app/page.tsx to consume the streamed /api/generate response.

Requirements:
- Track ProgressEvent[]
- Track elapsed time
- Track final GenerateResponse
- Move between generation stages based on streamed events
- Handle error and completion cleanly
```

**Done looks like:**

- The page can start generation and reflect streamed backend progress

---

**✅ Phase 10 done.** The frontend can now drive the backend workflow through streaming.

---

## Phase 11 — Results experience

> Goal: show the generated preview and provide PDF download.

---

### Task 11.1 — Implement PreviewSection.tsx

🤖 **Copilot**

Open `frontend/components/PreviewSection.tsx`. Paste:

```text
@workspace
Implement frontend/components/PreviewSection.tsx in full.

Requirements:
- Render sections differently based on section_type
- Support vocabulary, passages, learning targets, self-assessment, and answer key with tailored layouts
- Show warning or best-effort indicators when needed
```

---

### Task 11.2 — Implement WebPreview.tsx

🤖 **Copilot**

Open `frontend/components/WebPreview.tsx`. Paste:

```text
@workspace
Implement frontend/components/WebPreview.tsx in full.

Requirements:
- Accept WebPreviewPayload and ValidationResult
- Render sections in order using PreviewSection
- Surface warnings and validation summary clearly
```

---

### Task 11.3 — Implement DownloadButton.tsx

🤖 **Copilot**

Open `frontend/components/DownloadButton.tsx`. Paste:

```text
@workspace
Implement frontend/components/DownloadButton.tsx in full.

Requirements:
- Accept base64 PDF data and a filename
- Decode the PDF in the browser and trigger a file download
- Keep the interaction simple and reliable
```

---

### Task 11.4 — Finish the results layout in page.tsx

🤖 **Copilot**

Open `frontend/app/page.tsx`. Paste:

```text
@workspace
Complete the results state in frontend/app/page.tsx.

Requirements:
- Keep ProgressTracker visible after completion
- Render tabs or sections for Web Preview and Download PDF
- Show validation warnings when present
- Use a layout that works on both desktop and mobile
```

**Done looks like:**

- Users can review the generated guide and download the PDF from the UI

---

### Task 11.5 — Add iconography parity to the web preview

🤖 **Copilot**

Open `frontend/components/PreviewSection.tsx` and `frontend/components/WebPreview.tsx`. Paste:

```text
@workspace
Implement web preview iconography parity for the study-guide results UI.

Read ARCHITECTURE.md sections 8 and 9 before editing.

Requirements:
- Render the optional preview icon metadata using a local icon mapping
- Keep the visual language aligned with the PDF iconography treatment
- Support section headers and any approved repeated callout roles in the preview UI
- Degrade gracefully to text-only rendering when icon metadata is missing or unknown

Constraints:
- Do not fetch icons from remote URLs
- Do not introduce teacher-facing icon settings
- Preserve existing validation warning and best-effort indicators
```

**Done looks like:**

- The web preview renders the same iconography family as the PDF without changing content structure

---

**Phase 11 note.** The frontend results experience is feature-complete for the shipped prototype, and Task 11.5 extends it for iconography parity.

---

## Phase 12 — End-to-end validation and QA

> Goal: prove the app works against the documented must-haves.

---

### Task 12.1 — Run the full app locally

🧑 **You**

Start both runtimes:

```bash
# Backend
cd backend/study-guide-agent
uv run uvicorn app.fast_api_app:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev
```

Use the UI to submit a realistic lesson input and verify:

- The form submits successfully
- Progress updates stream visibly
- A preview is produced
- A PDF is downloadable

---

### Task 12.2 — Run scaffold-native evals

🧑 **You**

From `backend/study-guide-agent/`:

```bash
export PATH="/Users/joshuawenghao/.local/bin:$PATH"
agents-cli eval run
```

If you add more evalsets later, run them explicitly or use `--all`.

---

### Task 12.3 — Run backend tests

🧑 **You**

From `backend/study-guide-agent/`:

```bash
uv run pytest tests/unit tests/integration
```

Add narrower targeted test commands as needed during development.

---

### Task 12.4 — Verify IFC must-haves

🧑 **You**

Use `IFC.md` as the final must-have checklist.
Confirm at minimum:

- All required sections are generated in the correct order
- Dependency ordering is respected
- Hard validators run programmatically
- Retry behavior works for failed sections
- PDF layout is correct
- Answer key starts on a new page
- Market-aware and grade-appropriate generation is preserved
- No direct frontend Gemini calls exist

After each fully completed task or phase, update `TASK_STATUS.md`.

---

**✅ Phase 12 done.** The prototype has been implemented and validated against the repo’s documented requirements.

---

## Phase 13 — Deployment and parity

> Goal: make deployment repeatable before final feature completion, and make local reproduction mirror the remote topology closely enough to debug production-only failures.

This phase is cross-cutting. Do not wait until every Phase 13 task is finished before running deployment checks; execute the staged checkpoints when Phases 7, 10, and 12 reach the stated readiness levels.

---

### Task 13.1 — Document the deployment topology and environment matrix

🧑 **You**

Use `DEPLOYMENT.md`, `IFC.md`, and `ARCHITECTURE.md` as the deployment source of truth.
Confirm that the repo documents these modes clearly:

- fast local dev
- local parity
- remote staging
- production

Confirm the recommended production split remains:

- Firebase App Hosting for the frontend
- Cloud Run for the backend

**Done looks like:**

- `DEPLOYMENT.md` exists at the repo root
- The environment matrix and secret ownership are documented
- The staged deployment checkpoints are documented in the task plan

---

### Task 13.2 — Containerize the backend for Cloud Run parity

🧑 **You**

Use the existing backend Docker path as the starting point and verify it is suitable for both Cloud Run and local parity testing.

Confirm at minimum:

- WeasyPrint system dependencies are installed in the image
- the image boots `app.fast_api_app:app`
- runtime configuration comes from environment variables and not hardcoded values
- the same image can be run locally and on Cloud Run

**Done looks like:**

- A backend container can be built locally
- The container serves the backend on a configurable port
- The deployment guide documents the local and Cloud Run commands

---

### Task 13.3 — Add a local parity orchestration path

🧑 **You**

Create a repeatable local parity flow that runs the frontend in production mode and the backend in its Cloud Run-style container/runtime shape.

Possible implementation options:

- `docker compose`
- a repo script that builds and runs the backend container plus the production frontend
- another single-command wrapper with equivalent behavior

Whichever option you choose, keep the two-runtime split intact.

**Done looks like:**

- One documented command starts the parity stack
- The frontend talks to the backend through `ADK_BACKEND_URL`
- Production-only routing or CORS bugs can be reproduced locally without changing application code

---

### Task 13.4 — Configure the backend deployment for Cloud Run

🧑 **You**

Add the deployment configuration and documentation needed for a non-production and production Cloud Run service.

Capture at minimum:

- required environment variables and secret sources
- allowed origins for staging and production frontends
- request timeout and concurrency assumptions for long-running generation requests
- the deploy command or IaC entrypoint the repo will standardize on

**Done looks like:**

- The backend can be deployed to a staging Cloud Run service without manual code edits
- Staging and production origins are documented for CORS
- The deployment path is written down in `DEPLOYMENT.md`

---

### Task 13.5 — Configure the frontend deployment for Firebase App Hosting

🧑 **You**

Set up the frontend deployment path so the staging environment, and later production, can target the correct backend URL through environment configuration only.

Confirm at minimum:

- `ADK_BACKEND_URL` is set in Firebase App Hosting runtime configuration for staging, and later production if a production environment is introduced
- the Next.js proxy route stays thin and forwards to the backend URL without business logic
- the deployment guide documents which values belong in Firebase App Hosting configuration
- the chosen Firebase frontend target preserves Next.js server routes rather than forcing a static export

**Done looks like:**

- A Firebase App Hosting staging environment can talk to the staging Cloud Run backend
- A later production App Hosting environment can talk to the production Cloud Run backend without frontend code edits
- No frontend code changes are required when switching environments

---

### Task 13.6 — Run staged deployment checkpoints

🧑 **You**

Do not wait until the whole roadmap is complete before testing deployment.
Run these checkpoints when the corresponding phases are ready:

1. After Phase 7, deploy the backend to a dev environment and verify the service boots and accepts a representative request.
    Use the current non-production staging service when there is only one remote environment.
2. After Phase 10, deploy the integrated staging frontend plus staging backend and verify the proxy plus SSE path works remotely.
3. After Phase 12, deploy the release candidate and run a smoke test covering form submit, progress, preview, and PDF download.

Record the results in `TASK_STATUS.md` as you go.

**Done looks like:**

- Each checkpoint has been executed when its prerequisite phase was ready
- Deployment issues are found incrementally rather than at final release time
- The task tracker records which checkpoint was last validated

---

**✅ Phase 13 done.** Deployment is documented, parity tooling exists, and the repo has a repeatable staged path from local reproduction to managed cloud release.

---

## Phase 14 — Prompt Lab MVP
Phase 18 — Subject-agnostic deep dive

> Goal: add a private reviewer-only prompt-tuning workflow that reuses the shipped study-guide generator with request-scoped prompt overrides, without changing the teacher-facing default generation path.

This phase is product work, not deployment work. It should build on the existing teacher-facing generator, preview, and PDF pipeline instead of duplicating them.

---

### Task 14.1 — Extend the prompt-lab request contract and sample-input model

🧑 **You**

Implement the request shape needed for the private prompt-lab flow.

At minimum:

- add a backend model for `PromptLabGenerateRequest`
- mirror that contract in `frontend/lib/types.ts`
- define the supported prompt override shape clearly, including an explicit section allowlist
- define how curated sample lesson cases are identified in the request path

Keep the existing `GenerateRequest` and `GenerateResponse` contracts intact for the teacher-facing flow.

**Done looks like:**

- Backend and frontend both define the prompt-lab request contract
- Unsupported override keys are invalid by contract or rejected clearly at runtime
- The prompt-lab contract is documented as request-scoped only and not a persistent prompt store

---

### Task 14.2 — Add backend prompt override resolution for supported sections

🧑 **You**

Implement the backend layer that applies prompt-lab overrides to the existing workflow without mutating the default prompt templates on disk.

At minimum:

- keep the current system prompt and section prompt builders as the default path
- add a request-scoped override mechanism for the supported section allowlist
- allow optional system-prompt append behavior when present in the prompt-lab request
- keep validators, retry logic, section order, and rendering behavior unchanged

Prefer a narrow abstraction that wraps prompt construction rather than scattering conditionals across every node.

**Done looks like:**

- A prompt-lab request can alter supported prompt text for one run only
- A normal teacher-facing request still uses the unchanged default prompt path
- Unsupported or malformed overrides fail clearly without silently changing behavior

---

### Task 14.3 — Add a prompt-lab backend endpoint and thin frontend proxy route

🧑 **You**

Add the dedicated transport layer for the reviewer-only flow.

At minimum:

- expose a backend prompt-lab generate endpoint or equivalent request surface
- add `frontend/app/api/prompt-lab/generate/route.ts` as a thin proxy
- stream the same `ProgressEvent` contract used by the teacher flow
- return the same `GenerateResponse` contract on completion

Do not merge prompt-lab handling into the teacher-facing `/api/generate` route if it makes the public flow harder to reason about.

**Done looks like:**

- Prompt-lab requests can run end to end through a dedicated proxy path
- SSE progress and final result handling stay contract-compatible with the existing frontend components
- The teacher-facing route remains thin and behaviorally isolated

---

### Task 14.4 — Add curated prompt-lab sample inputs

🧑 **You**

Create the initial small set of structured lesson cases used for reviewer experiments.

At minimum:

- define a small curated sample set covering representative lesson shapes
- store the sample data in a stable repo location appropriate for internal reviewer tooling
- make each sample resolvable by a simple identifier used by the prompt-lab UI

Keep the MVP small. A few representative cases are enough to support reviewer iteration.

**Done looks like:**

- The prompt-lab flow can preload a curated sample by id
- The sample set is documented and uses the existing study-guide request structure
- The sample data is clearly separate from teacher-facing runtime defaults

---

### Task 14.5 — Build the private prompt-lab page and reviewer editors

🧑 **You**

Add the dedicated reviewer page in the frontend.

At minimum:

- add `frontend/app/prompt-lab/page.tsx`
- add UI for selecting a sample case or editing the underlying request values
- add plain-text prompt editors for the supported override allowlist
- keep the page out of the main teacher-facing navigation in the MVP

The page should be understandable to non-technical reviewers. Do not expose Python module names or implementation details in the UI.

**Done looks like:**

- A reviewer can choose a sample case, edit supported prompt text, and submit a run from one page
- The page is clearly separate from the normal teacher generation flow
- The page is usable without repo or terminal knowledge

---

### Task 14.6 — Reuse progress, preview, download, and validation results in prompt lab

🧑 **You**

Wire the prompt-lab page into the existing generation-result experience wherever reuse is practical.

At minimum:

- show streamed progress during a prompt-lab run
- render the returned web preview
- expose the generated PDF download
- surface validation warnings and best-effort indicators just as clearly as the teacher flow

Prefer reusing existing result components over creating a second results system.

**Done looks like:**

- Prompt-lab results are reviewable with the same core fidelity as the teacher-facing generator
- Reviewers can assess whether prompt wording improved the output without extra tooling
- Existing preview and result components remain the canonical rendering path where practical

---

### Task 14.7 — Add focused prompt-lab validation and documentation

🧑 **You**

Validate the new reviewer flow with focused checks and update repo docs where implementation details became real.

At minimum:

- add focused backend tests for prompt override application and rejection of unsupported keys
- add focused frontend checks for the prompt-lab page state and request shaping
- run an end-to-end prompt-lab smoke path using at least one curated sample
- refresh any user-facing or repo-facing docs needed to explain the prompt-lab MVP once implemented

Keep validation scoped to the prompt-lab slice rather than rerunning the entire roadmap without reason.

**Done looks like:**

- Prompt-lab-specific tests or smoke checks exist and pass
- The reviewer flow is documented at the appropriate level for this repo
- `TASK_STATUS.md` can record the feature as implemented with a concrete validation trail

---

**✅ Phase 14 done.** The repo includes a private prompt-lab MVP that lets non-technical reviewers test request-scoped prompt variants against the real generator without repo access and without altering the default teacher-facing prompt path.

---

## Phase 20 — Resilience hardening (P0 + P1)

> Goal: close the most impactful fault-tolerance gaps identified in the resilience audit — silent frontend hangs, Gemini quota failures under retries, concurrent-user overload, and insufficient section-retry passes.

---

### Task 20.1 — P0: Frontend idle timeout and Gemini exponential backoff

Two single-file fixes that address the two highest-priority unhandled failure modes.

**Frontend idle timeout (`frontend/app/page.tsx`)**

- Add an idle timeout ref (e.g. `idleTimerRef`) that is set to a `setTimeout` firing after 90 seconds on each SSE event and cleared on each new event.
- On expiry, call `abortController.abort()`, set stage to `"error"`, and set a user-facing error message such as `"Generation stalled — no progress for 90 seconds. Please try again."`.
- Clear the timer in the same cleanup function that already calls `abortController.abort()`.
- Do not add any new dependencies or libraries.

**Gemini exponential backoff (`backend/study-guide-agent/app/nodes/base.py`)**

- Replace the flat `asyncio.sleep(1)` in the `call_gemini` retry loop with exponential backoff: `asyncio.sleep(2 ** attempt)` (1 s, 2 s, 4 s for attempts 0, 1, 2).
- Detect HTTP 429 responses specifically (check `error` string or exception type for `"429"` or `"RESOURCE_EXHAUSTED"`) and use a longer base: `asyncio.sleep(min(60, 4 ** attempt))` for rate-limit errors (4 s, 16 s, 60 s).
- All other errors keep the standard `2 ** attempt` schedule.
- Keep `max_retries=2` (3 total attempts) unchanged.
- Log the error type and backoff duration at `WARNING` level before each sleep.

**Validation:**

```bash
cd backend/study-guide-agent && uv run pytest tests/unit/test_base_gemini_wrapper.py -q
./scripts/validate-task.sh
```

**Done looks like:**

- The frontend never hangs silently for more than 90 seconds — it shows an error and lets the user retry.
- `call_gemini` sleeps for 2^attempt seconds on generic errors and 4^attempt (capped at 60 s) on 429/RESOURCE_EXHAUSTED errors.
- Existing backend tests still pass.

---

### Task 20.2 — P1: Concurrency limiter and increased section retry passes

Two backend changes that protect against concurrent-user overload and improve generation quality under failures.

**Concurrency limiter (`backend/study-guide-agent/app/fast_api_app.py`)**

- Add a module-level `asyncio.Semaphore` with a cap of 5 concurrent workflows (constant `MAX_CONCURRENT_WORKFLOWS = 5`).
- In the `/generate` (and `/prompt-lab/generate`) SSE endpoint handler, acquire the semaphore before creating the workflow task and release it in the `finally` block.
- If the semaphore cannot be acquired immediately (i.e. all slots are taken), return HTTP 503 with a JSON body `{"error": "Server busy — too many concurrent generations. Please retry in a moment."}` before entering the SSE stream.
- Use `asyncio.Semaphore.locked()` or a non-blocking `acquire` with `timeout=0` to detect full capacity without blocking the request handler.
- Do not add any queue — reject at capacity.

**Increased section retry passes (`backend/study-guide-agent/app/agent.py`)**

- Change the retry loop guard from `retry_count < 1` to `retry_count < 3` so failed sections get up to 3 retry passes instead of 1.
- After each retry pass that produces newly passing sections, log `f"Retry pass {retry_count}: {len(newly_passed)} sections recovered"` at `INFO` level.
- After subconcept retries inside `_generate_retry_payload`, re-validate the subconcept outputs individually using the existing `json_schema` hard validator so a still-broken subconcept is not silently promoted to `best_effort`.

**Validation:**

```bash
cd backend/study-guide-agent && uv run pytest tests/unit tests/integration -q
./scripts/validate-task.sh
```

**Done looks like:**

- A sixth simultaneous `/generate` request receives HTTP 503 while 5 are active.
- Failed sections are retried up to 3 times before being demoted to `best_effort`.
- Subconcept outputs are individually re-validated after retries.
- All existing backend tests still pass.

---

**✅ Phase 20 done.** The app no longer hangs silently on backend stalls, handles Gemini quota errors more gracefully, rejects excess concurrent load cleanly, and makes more retry attempts before giving up on failed sections.

---

## Recommended operating pattern for future chats

When starting a new Copilot chat for implementation:

1. Ask Copilot to read `TASKS.md`, `TASK_STATUS.md`, `ARCHITECTURE.md`, `IFC.md`, and `.github/copilot-instructions.md` first.
2. Have Copilot choose the next incomplete or partial task from `TASK_STATUS.md`.
3. Implement one focused slice at a time.
4. Validate immediately after each substantive change.
5. Update `TASK_STATUS.md` only when implementation and validation both exist.

## Summary

- `TASKS.md` remains the detailed, stable implementation guide.
- `TASK_STATUS.md` remains the lightweight progress snapshot.
- The scaffolded backend under `backend/study-guide-agent/` is the only backend target for future work.
- Prompt-lab MVP work starts only after reading the Phase 14 task slice alongside the prompt-lab requirements now recorded in `IFC.md` and `ARCHITECTURE.md`.

---

## Phase 18 — Subject-agnostic deep dive

> Goal: remove the hardcoded ELA author's-purpose framing (entertain / inform / persuade) from the deep dive section and replace it with a blueprint-driven compare/contrast structure that works across all subjects, including nursing.

This phase touches the backend data contract, both prompt templates, the HTML renderer, and the React preview component. The `TopicDomains` type loses its three ELA-specific fields; a new `deep_dive_dimensions` list on `Blueprint` carries subject-appropriate dimension labels generated by the blueprint node.

---

### Task 18.1 — Remove ELA-hardcoded fields and rewrite backend prompts

🧑 **You**

Update the backend data contract and both affected prompt templates so the deep dive section works for any subject.

At minimum:

- remove `entertain_example`, `inform_example`, `persuade_example` from `TopicDomains` in `backend/study-guide-agent/app/types.py`
- add `deep_dive_dimensions: list[str]` as a top-level field on the `Blueprint` model in `types.py`
- rename `DeepDiveExample.mode` → `DeepDiveExample.dimension` and `DeepDiveExample.signal_words` → `DeepDiveExample.key_terms` in `types.py`
- update `prompts/templates/blueprint.py`: remove the three ELA fields from the schema and instructions; add `deep_dive_dimensions` as a string array; instruct Gemini to generate 2–4 subject-appropriate contrast dimension labels
- rewrite `prompts/templates/deep_dive.py`: read `blueprint.deep_dive_dimensions` dynamically; remove all hardcoded ELA framing; update the output schema to use `dimension` and `key_terms`
- update all backend unit test fixtures that instantiate `TopicDomains` (remove the three removed fields): `tests/unit/test_vocab_presence_validator.py`, `tests/unit/test_wave1_section_nodes.py`
- add a focused unit test asserting that the deep dive prompt builder includes each dimension from `blueprint.deep_dive_dimensions` and contains no hardcoded ELA strings for a non-ELA subject fixture
- update `ARCHITECTURE.md` section 6 (Blueprint contract): remove the three ELA fields from `topic_domains`; document `deep_dive_dimensions`; update the `DeepDiveExample` shape

Do not touch the HTML renderer or React preview in this task — those renames happen in Task 18.2.

**Done looks like:**

- `uv run pytest tests/unit/ -q` passes from `backend/study-guide-agent/`
- Pyright reports 0 errors on the backend
- `TopicDomains` has exactly two fields (`model_passage`, `assessment_passage`)
- `Blueprint` has a `deep_dive_dimensions` field
- The deep dive prompt reads dimensions dynamically from the blueprint
- `ARCHITECTURE.md` reflects the new contract

---

### Task 18.2 — Align renderer and frontend preview to new field names

🧑 **You**

Update the HTML renderer template and React preview component to consume the renamed fields from Task 18.1.

At minimum:

- update `backend/study-guide-agent/app/templates/study_guide.html.j2`: replace `example.mode` with `example.dimension`, `example.signal_words` with `example.key_terms`, and the "Signal words" label text with "Key terms"
- update `backend/study-guide-agent/tests/unit/test_renderer.py`: update the `TopicDomains` fixture (remove three removed fields); update the deep dive fixture to use `dimension` and `key_terms`; add `deep_dive_dimensions` to any Blueprint fixture that is missing it
- update `frontend/components/PreviewSection.tsx`: replace `getString(example, "mode")` with `getString(example, "dimension")`, `getStringArray(example, "signal_words")` with `getStringArray(example, "key_terms")`, and the "Signal words" label with "Key terms"
- update `frontend/components/PreviewSection.test.tsx`: update the deep dive fixture to use `dimension` and `key_terms`

**Done looks like:**

- `./scripts/validate-task.sh` passes from the repo root
- The PDF renderer and React web preview both render deep dive examples using the `dimension` heading and a "Key terms" label
- No references to `signal_words`, `mode` (as a deep dive field), `entertain_example`, `inform_example`, or `persuade_example` remain in active code paths

---

## Phase 19 — Soft Validator Quality Improvements

> Goal: reduce noisy false-positive warnings and improve the accuracy of the reading-level soft validator so generated warnings are more actionable.

---

### Task 19.1 — Settle reading-level metric on Flesch-Kincaid with widened tolerance bands

Calibrate the readability metric and tolerance bands in `backend/study-guide-agent/app/validators/soft/reading_level.py` so generated study-guide prose produces actionable warnings rather than systematic false positives.

The original plan was to switch to Dale-Chall for grades ≤ 8; Linsear Write was trialled and produced consistently higher scores than FK for academic K–12 prose (binary 3-syllable penalty over-penalises multi-syllabic subject vocabulary). The settled implementation retains FK throughout all grades, implemented via pyphen-based syllable counting (`textstat.backend.utils._get_pyphen`), and widens tolerance bands to match observed FK scores for curriculum-aligned content.

Tolerance bands:
- Base: 1.5 for grades ≤ 4, 2.0 for grades 5+
- `deep_dive` bonus: +0.5 (complex by design)
- `assessment_passage` bonus: +0.5 (different topic domain expected to vary in register)
- `intro` (grade ≤ 6) bonus: +0.5

**Done looks like:**

- `validate_reading_level` uses `_flesch_kincaid_grade()` (pyphen-based) for all grade levels
- `_warning_tolerance()` implements the bands above
- Unit tests in `tests/unit/test_reading_level_validator.py` pass
- `./scripts/validate-task.sh` passes

---

### Task 19.2 — Fix tolerance curve for grades 5+

In `_warning_tolerance()` in `backend/study-guide-agent/app/validators/soft/reading_level.py`, raise the base tolerance for grades 5+ to 2.0 so the validator does not fire on content that is only marginally above the target grade. Earlier intermediate step set it to 1.25; the final shipped value is 2.0 to reflect that FK naturally scores curriculum-aligned prose ~2 grade levels above target due to domain vocabulary.

---

### Task 19.3 — Remove model_passage from reading-level checked sections

Remove `"model_passage"` from `PROSE_SECTION_KEYS` in `backend/study-guide-agent/app/validators/soft/reading_level.py`. The hard validator already guarantees that `model_passage` has a different topic domain from the lesson; its reading level does not need to track the lesson grade target and checking it produces domain-mismatch noise.

**Done looks like:**

- `PROSE_SECTION_KEYS` no longer contains `"model_passage"`
- Any unit test that references `model_passage` in the reading-level validator is updated
- `./scripts/validate-task.sh` passes

---

### Task 19.4 — Expand answer leakage excluded sections

Add `"model_passage"`, `"check_in"`, `"learning_targets"`, `"strategy_list"`, and `"self_assessment"` to `EXCLUDED_SECTION_KEYS` in `backend/study-guide-agent/app/validators/soft/answer_leakage.py`. These sections are structurally disconnected from the assessment passage by design and currently produce false-positive warnings that bury genuine leakage in `core_explainer`, `subconcept`, and `deep_dive`.

**Done looks like:**

- `EXCLUDED_SECTION_KEYS` contains all 8 sections: the original 3 plus the 5 new ones
- At least one new unit test in `tests/unit/test_answer_leakage_validator.py` verifies that a leaked phrase in one of the 5 newly excluded sections does not trigger a warning
- `./scripts/validate-task.sh` passes

---

### Task 19.5 — Add minimum phrase length filter to answer leakage validator

In `_extract_quoted_phrases()` in `backend/study-guide-agent/app/validators/soft/answer_leakage.py`, filter out extracted phrases shorter than 5 words before returning them. Short quoted phrases (2–3 words) can match common collocations in instructional body text that are unrelated to actual answer leakage, generating noise that obscures real warnings.

**Done looks like:**

- `_extract_quoted_phrases` only returns phrases where `len(phrase.split()) >= 5`
- A new unit test verifies that a phrase with fewer than 5 words does not trigger a leakage warning even when it appears in a checked section
- `./scripts/validate-task.sh` passes
