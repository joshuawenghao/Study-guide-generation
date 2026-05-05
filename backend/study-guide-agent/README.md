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

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
uv run uvicorn app.fast_api_app:app --reload --host 0.0.0.0 --port 8000
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`, or use `agents-cli playground` for the scaffolded agent playground.

## Commands

| Command                                      | Description                          |
| -------------------------------------------- | ------------------------------------ |
| `agents-cli install`                         | Install dependencies using uv        |
| `agents-cli playground`                      | Launch local development environment |
| `agents-cli lint`                            | Run code quality checks              |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests       |

## 🛠️ Project Management

| Command                       | What It Does                                                   |
| ----------------------------- | -------------------------------------------------------------- |
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure               |
| `agents-cli infra cicd`       | One-command setup of entire CI/CD pipeline + infrastructure    |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

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

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.
