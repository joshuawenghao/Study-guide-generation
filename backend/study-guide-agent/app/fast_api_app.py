# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ruff: noqa: E402

import asyncio
import json
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.cli.fast_api import get_fast_api_app

from app.agent import study_guide_workflow
from app.app_utils.telemetry import setup_telemetry
from app.prompt_lab.samples import get_prompt_lab_sample, list_prompt_lab_samples
from app.types import (
    GenerateRequest,
    GenerateResponse,
    ProgressEvent,
    PromptLabGenerateRequest,
    PromptLabSampleInput,
    StudyGuideRequest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

setup_telemetry()

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAX_CONCURRENT_WORKFLOWS = 5
_workflow_semaphore = asyncio.Semaphore(MAX_CONCURRENT_WORKFLOWS)


def _get_optional_env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = _get_optional_env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_allowed_origins() -> list[str] | None:
    raw_value = _get_optional_env("BACKEND_CORS_ALLOW_ORIGINS")
    if raw_value is None:
        return None
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    return origins or None


session_service_uri = _get_optional_env("SESSION_SERVICE_URI")
artifact_service_uri = _get_optional_env("ARTIFACT_SERVICE_URI")
allow_origins = _get_allowed_origins()
trace_to_cloud = _get_bool_env("TRACE_TO_CLOUD")
otel_to_cloud = _get_bool_env("OTEL_TO_CLOUD")

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    trace_to_cloud=trace_to_cloud,
    otel_to_cloud=otel_to_cloud,
)
app.title = "study-guide-agent"
app.description = "API for interacting with the study guide generation agent"


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _normalize_node_name(node_name: str) -> str:
    if node_name in {"blueprint_node", "generate_blueprint"}:
        return "blueprint"
    if node_name.startswith("_generate_") and node_name.endswith("_node"):
        return node_name[len("_generate_") : -len("_node")]
    if node_name.endswith("_workflow_node"):
        return node_name[: -len("_workflow_node")]
    if node_name.startswith("retry_"):
        suffix = node_name[len("retry_") :]
        retry_parts = suffix.rsplit("_", maxsplit=1)
        return retry_parts[0] if len(retry_parts) == 2 else suffix
    return node_name


class _StreamingWorkflowContext:
    def __init__(self, emit_event: Any) -> None:
        self._emit_event = emit_event

    async def run_node(self, node: Any, node_input: Any = None) -> Any:
        raw_name_like = getattr(node, "name", type(node).__name__)
        raw_name = (
            raw_name_like if isinstance(raw_name_like, str) else type(node).__name__
        )
        node_name = _normalize_node_name(raw_name)

        event_type = "node_started"
        if raw_name.startswith("retry_"):
            event_type = "retry_started"
        elif node_name == "validation":
            event_type = "validation_started"
        elif node_name == "render":
            event_type = "render_started"

        await self._emit_event(
            "progress",
            ProgressEvent(
                type=event_type,
                node=node_name,
                timestamp=_timestamp(),
            ).model_dump(mode="json"),
        )

        node_func = cast(_SingleInputNodeProtocol, node)._func
        result = await node_func(node_input)

        await self._emit_event(
            "progress",
            ProgressEvent(
                type="node_complete",
                node=node_name,
                timestamp=_timestamp(),
            ).model_dump(mode="json"),
        )
        return result


async def _stream_workflow(request: StudyGuideRequest) -> StreamingResponse:
    if _workflow_semaphore.locked():
        raise HTTPException(
            status_code=503,
            detail="Server busy — too many concurrent generations. Please retry in a moment.",
        )
    await _workflow_semaphore.acquire()

    event_queue: asyncio.Queue[tuple[str, dict[str, Any]] | None] = asyncio.Queue()

    async def emit_event(event_name: str, payload: dict[str, Any]) -> None:
        await event_queue.put((event_name, payload))

    async def run_workflow() -> None:
        try:
            workflow_context = _StreamingWorkflowContext(emit_event)
            workflow_func = cast(_WorkflowNodeProtocol, study_guide_workflow)._func
            result = await workflow_func(workflow_context, request)
            await emit_event(
                "progress",
                ProgressEvent(
                    type="done",
                    node="workflow",
                    timestamp=_timestamp(),
                ).model_dump(mode="json"),
            )
            await emit_event("result", result.model_dump(mode="json"))
        except Exception as exc:  # pragma: no cover - exercised via streaming test
            await emit_event(
                "progress",
                ProgressEvent(
                    type="error",
                    node="workflow",
                    message=str(exc),
                    timestamp=_timestamp(),
                ).model_dump(mode="json"),
            )
            await emit_event("error", {"error": str(exc)})
        finally:
            await event_queue.put(None)

    workflow_task = asyncio.create_task(run_workflow())

    async def event_generator() -> AsyncIterator[str]:
        try:
            while True:
                event = await event_queue.get()
                if event is None:
                    break

                event_name, payload = event
                yield f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"
        finally:
            _workflow_semaphore.release()
            if not workflow_task.done():
                workflow_task.cancel()
                with suppress(asyncio.CancelledError):
                    await workflow_task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
        },
    )


@app.post("/generate")
async def generate(request: GenerateRequest) -> StreamingResponse:
    return await _stream_workflow(request)


@app.post("/prompt-lab/generate")
async def generate_prompt_lab(request: PromptLabGenerateRequest) -> StreamingResponse:
    return await _stream_workflow(request)


@app.get("/prompt-lab/samples", response_model=list[PromptLabSampleInput])
async def prompt_lab_samples() -> list[PromptLabSampleInput]:
    return list_prompt_lab_samples()


@app.get("/prompt-lab/samples/{sample_id}", response_model=PromptLabSampleInput)
async def prompt_lab_sample(sample_id: str) -> PromptLabSampleInput:
    try:
        return get_prompt_lab_sample(sample_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail="Prompt-lab sample not found."
        ) from exc


class _SingleInputNodeProtocol(Protocol):
    _func: Callable[[Any], Awaitable[Any]]


class _WorkflowNodeProtocol(Protocol):
    _func: Callable[[Any, StudyGuideRequest], Awaitable[GenerateResponse]]


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
