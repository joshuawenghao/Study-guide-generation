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
```

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

3. MODEL_NAME = "gemini-2.0-flash"

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
- Use model="gemini-2.0-flash"
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

**✅ Phase 2 done.** Shared types are now stable enough for prompts, nodes, validators, and frontend flows.

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

**✅ Phase 6 done.** Rendering is now testable and aligned with the product contract.

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

**✅ Phase 11 done.** The frontend is feature-complete for the prototype experience.

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
