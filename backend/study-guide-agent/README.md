# study-guide-agent

Study guide generation agent scaffold migrated from the legacy backend prototype.
Agent generated with `agents-cli` version `0.1.2`

## Project Structure

```
study-guide-agent/
├── app/         # Core agent code
│   ├── agent.py               # Main ADK entrypoint
│   ├── fast_api_app.py        # FastAPI entrypoint for the backend HTTP server
│   ├── types.py               # Shared Pydantic data contracts
│   ├── nodes/                 # Workflow nodes and section placeholders
│   ├── prompts/               # Prompt modules and template placeholders
│   ├── validators/            # Hard and soft validator placeholders
│   ├── templates/             # Renderer template placeholders
│   └── app_utils/             # Scaffold-provided helpers
├── tests/                     # Unit, integration, and load tests
│   ├── eval/evalsets/         # agents-cli evalsets
│   └── fixtures/legacy_evals/ # Preserved legacy study-guide eval JSON fixtures
├── AGENTS.md                  # AI-assisted development guide
└── pyproject.toml             # Project dependencies
```

The scaffolded coding-agent guidance for this project is in `AGENTS.md`.

## Requirements

Before you begin, ensure you have:

- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)

## Quick Start

If `agents-cli` is not on your shell `PATH`, use the repo-local wrapper from this directory:

```bash
./agents-cli --help
./agents-cli install
./agents-cli info
```

This wrapper delegates to the globally installed CLI at `$HOME/.local/bin/agents-cli`, so you do not need to copy the CLI or its skills into the repository.

Minimal setup for this repo:

- Keep the global CLI install (`uv tool install google-agents-cli`)
- Use `./agents-cli ...` from this directory if your shell cannot find `agents-cli`
- Do not run `./agents-cli setup --workspace` unless you explicitly want workspace-local skill adapters for multiple coding agents

Why this is the minimal set:

- The backend project commands (`install`, `info`, `playground`, `deploy`) only need the CLI binary
- The Google skills do not need to be copied into this repository for normal CLI usage
- `setup --workspace` generates per-tool adapter folders like `.claude/`, `.continue/`, `.windsurf/`, `.agents/`, and `skills/`, which are useful only if you want this repo itself to carry local coding-agent integrations

If you want workspace-local skills again later, rerun:

```bash
./agents-cli setup --workspace
```

If you just want the CLI commands and a cleaner repo, the current setup is enough.

Install required packages:

```bash
./agents-cli install
```

Create the backend environment file in the scaffolded project root:

```bash
cp .env.example .env
```

The backend runtime reads `backend/study-guide-agent/.env` automatically for local runs. At minimum set `GOOGLE_API_KEY`; `MARKET_DEFAULT=PH` is included as the default market.

To enable the primary English reading-level path locally, install the NLTK `cmudict` corpus into a project-local data directory:

```bash
mkdir -p .nltk_data
NLTK_DATA=$PWD/.nltk_data uv run python -c "import nltk; nltk.download('cmudict', download_dir='$PWD/.nltk_data')"
```

The reading-level validator will auto-detect `backend/study-guide-agent/.nltk_data/` when it exists. If the corpus is missing, the validator falls back to a local Pyphen-based estimate instead of skipping analysis.

Test the agent with a local web server:

```bash
uv run uvicorn app.fast_api_app:app --reload --host 0.0.0.0 --port 8000
```

On macOS, the renderer now auto-resolves common Homebrew WeasyPrint libraries from `/opt/homebrew/opt` and `/usr/local/opt` before importing WeasyPrint. The local PDF path still expects the relevant formulas to be installed, but you no longer need to hand-wire library paths just to run the study-guide UI or demo flow.

Generate local demo PDFs without starting the server:

```bash
uv run python run_demo.py --mode renderer-only
uv run python run_demo.py --mode full-workflow
open demo-output/study-guide-full-demo.pdf
```

By default, generated PDFs are written under `backend/study-guide-agent/demo-output/`, which makes them easy to find in the workspace and open from Finder or VS Code.

Customize the full-workflow demo with teacher-style input values while keeping a default when no custom file is provided:

```bash
uv run python run_demo.py --print-default-input
uv run python run_demo.py --mode full-workflow --input path/to/custom-input.json
uv run python run_demo.py --mode full-workflow --open
```

The custom input file may contain either the full `GenerateRequest` JSON object or a partial override that only includes the fields you want to change. Partial overrides are merged onto the default fixture so you can vary a lesson title, grade level, curriculum, or optional hints without rebuilding the whole payload.

The `renderer-only` mode proves Jinja2 plus WeasyPrint PDF rendering without calling Gemini. The `full-workflow` mode runs the real workflow against `tests/fixtures/legacy_evals/english_grade6_ph.json` and auto-loads `backend/study-guide-agent/.env` for `GOOGLE_API_KEY` during local runs.

The `full-workflow` JSON summary now includes both `validation_warning_count` and `validation_warnings`, which makes it easier to inspect remaining soft-validator output from the terminal without opening the PDF first.

The prompt-lab sample catalog now lives under `app/prompt_lab/sample_inputs/` and currently includes five checked-in reviewer cases: Grade 6 English (PH), Grade 4 Math (VN), Grade 12 Nursing/Health (PH), Grade 8 Science (PH), and Grade 7 Social Studies (PH). The backend exposes these through `/prompt-lab/samples` and `/prompt-lab/samples/{sample_id}` so the shipped private reviewer UI at `frontend/app/prompt-lab/page.tsx` can preload curated requests by stable id.

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`, or use `agents-cli playground` for the scaffolded agent playground.

Scaffold-native conversational CLI and eval flows now run through the dedicated `eval_app/` loader surface, while the real typed study-guide workflow used by the backend `/generate` endpoint remains under `app/agent.py` and the ADK loader compatibility package remains `study_guide_agent/`.

This keeps `app/` as implementation code for the real generator instead of overloading it as both a product package and a conversational eval surface.

Run the scaffold-native evalset from this directory with:

```bash
export PATH="$HOME/.local/bin:$PATH"
./agents-cli eval run
```

For simple local conversational spot checks, you can also run:

```bash
./agents-cli run "What kind of study guides can you generate for teachers?"
```

The repo-local wrapper routes these local chat and eval commands to `./eval_app`, and the current evalset under `tests/eval/evalsets/basic.evalset.json` therefore uses the ADK app name `eval_app`.

## Commands

| Command                                      | Description                          |
| -------------------------------------------- | ------------------------------------ |
| `./agents-cli install`                       | Install dependencies using uv        |
| `./agents-cli playground`                    | Launch local development environment |
| `./agents-cli lint`                          | Run code quality checks              |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests       |
| `uv run pytest tests/unit/test_prompt_lab_prompt_overrides.py tests/unit/test_prompt_lab_types.py tests/integration/test_server_e2e.py -k prompt_lab -q` | Run focused prompt-lab checks |

## Test Warning Policy

This backend currently depends on `google-adk>=2.0.0b1,<2.1.0`, so some upstream classes still emit experimental `UserWarning`s during pytest collection and execution.

The repo config filters the two known Google ADK credential-service warnings:

- `[EXPERIMENTAL] InMemoryCredentialService`
- `[EXPERIMENTAL] BaseCredentialService`

This is only to keep routine test output readable. It does not suppress unrelated warnings, and it should be revisited when the ADK dependency is upgraded.

## 🛠️ Project Management

| Command                         | What It Does                                                   |
| ------------------------------- | -------------------------------------------------------------- |
| `./agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure               |
| `./agents-cli infra cicd`       | One-command setup of entire CI/CD pipeline + infrastructure    |
| `./agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and build the study-guide workflow out under `app/nodes/`.

## Migrated From The Old Backend

The scaffold now mirrors the old backend structure inside `app/`, including placeholder files that are intended to be implemented later:

- `backend/types.py` -> `app/types.py`
- `backend/nodes/base.py` -> `app/nodes/base.py`
- `backend/nodes/` -> `app/nodes/`
- `backend/prompts/` -> `app/prompts/`
- `backend/validators/` -> `app/validators/`
- `backend/templates/study_guide.html.j2` -> `app/templates/study_guide.html.j2`
- `backend/study_guide_agent/.env.example` -> `.env.example`
- `backend/evals/*.json` -> `tests/fixtures/legacy_evals/*.json`

This means future implementation work can happen entirely inside the scaffolded project instead of being split between the old backend root and `study-guide-agent`.

## Evaluation Files

There are now two evaluation layers in the scaffolded project:

- `tests/eval/evalsets/` contains agents-cli evalsets used by `agents-cli eval run`.
- `tests/fixtures/legacy_evals/` contains the original study-guide acceptance fixtures migrated from the old backend. These are preserved as structured reference cases and future custom test inputs.

## Legacy Files You Can Remove

The duplicated legacy backend tree has already been removed. The canonical backend is now `backend/study-guide-agent/`.

The old `backend/evals/` JSON files were not discarded; they now live under `tests/fixtures/legacy_evals/`.

## Deployment

The repo-level deployment source of truth is `DEPLOYMENT.md` in the repository root. Use this backend README only for the backend-specific command surface.

Recommended target:

- frontend on Vercel
- backend on Google Cloud Run

The backend should also be runnable locally in the same container/runtime shape intended for Cloud Run so production issues can be reproduced without changing backend code.

```bash
GCP_PROJECT_ID=<your-project-id> \
CLOUD_RUN_REGION=<your-region> \
BACKEND_CORS_ALLOW_ORIGINS=http://localhost:3000 \
./scripts/deploy-backend-cloud-run.sh dev --dry-run
```

The backend runtime reads deployment configuration from environment variables rather than code edits. The deployment-facing variables are documented in the repo-level `DEPLOYMENT.md`, including `BACKEND_CORS_ALLOW_ORIGINS`, the Cloud Run timeout and concurrency defaults, and the script-supported secret/env overrides.

The standardized backend deploy entrypoint is `./scripts/deploy-backend-cloud-run.sh <dev|prod>`. Use `--dry-run` to print the exact `gcloud run deploy` command without executing it.

To add CI/CD and Terraform, run `./agents-cli scaffold enhance`.
To set up your production infrastructure, run `./agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.
