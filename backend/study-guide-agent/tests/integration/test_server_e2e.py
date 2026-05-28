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

import logging
import os
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
import requests
from requests.exceptions import RequestException

import app.fast_api_app as fast_api_module
from app.types import GenerateResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000/"
STREAM_URL = BASE_URL + "run_sse"

HEADERS = {"Content-Type": "application/json"}


def log_output(pipe: Any, log_func: Any) -> None:
    """Log the output from the given pipe."""
    for line in iter(pipe.readline, ""):
        log_func(line.strip())


def start_server() -> subprocess.Popen[str]:
    """Start the FastAPI server using subprocess and log its output."""
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.fast_api_app:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    env = os.environ.copy()
    env["INTEGRATION_TEST"] = "TRUE"
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )

    # Start threads to log stdout and stderr in real-time
    threading.Thread(
        target=log_output, args=(process.stdout, logger.info), daemon=True
    ).start()
    threading.Thread(
        target=log_output, args=(process.stderr, logger.error), daemon=True
    ).start()

    return process


def wait_for_server(timeout: int = 90, interval: int = 1) -> bool:
    """Wait for the server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get("http://127.0.0.1:8000/docs", timeout=10)
            if response.status_code == 200:
                logger.info("Server is ready")
                return True
        except RequestException:
            pass
        time.sleep(interval)
    logger.error(f"Server did not become ready within {timeout} seconds")
    return False


@pytest.fixture(scope="session")
def server_fixture(request: Any) -> Iterator[subprocess.Popen[str]]:
    """Pytest fixture to start and stop the server for testing."""
    logger.info("Starting server process")
    server_process = start_server()
    if not wait_for_server():
        pytest.fail("Server failed to start")
    logger.info("Server process started")

    def stop_server() -> None:
        logger.info("Stopping server process")
        server_process.terminate()
        server_process.wait()
        logger.info("Server process stopped")

    request.addfinalizer(stop_server)
    yield server_process


def test_docs_and_session_endpoints(server_fixture: subprocess.Popen[str]) -> None:
    """Test that the server boots and exposes the base session surface."""
    logger.info("Starting docs and session endpoint test")
    del server_fixture

    docs_response = requests.get(f"{BASE_URL}/docs", timeout=30)
    assert docs_response.status_code == 200

    user_id = "test_user_123"
    session_data = {"state": {"preferred_language": "English", "visit_count": 1}}

    session_url = f"{BASE_URL}/apps/study_guide_agent/users/{user_id}/sessions"
    session_response = requests.post(
        session_url,
        headers=HEADERS,
        json=session_data,
        timeout=60,
    )
    assert session_response.status_code == 200
    session_payload = session_response.json()
    logger.info(f"Session creation response: {session_payload}")
    assert session_payload["appName"] == "study_guide_agent"
    assert session_payload["userId"] == user_id
    assert session_payload["id"]


def test_chat_stream_error_handling(server_fixture: subprocess.Popen[str]) -> None:
    """Test the chat stream error handling."""
    logger.info("Starting chat stream error handling test")
    data = {
        "input": {"messages": [{"type": "invalid_type", "content": "Cause an error"}]}
    }
    response = requests.post(
        STREAM_URL, headers=HEADERS, json=data, stream=True, timeout=10
    )

    assert response.status_code == 422, (
        f"Expected status code 422, got {response.status_code}"
    )
    logger.info("Error handling test completed successfully")


def test_generate_route_streams_progress_and_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_payload = {
        "lesson_metadata": {
            "subject": "English",
            "grade_level": 6,
            "market": "PH",
            "language": "en",
            "unit_number": 2,
            "unit_title": "Reading with Purpose",
            "lesson_number": 1,
            "lesson_title": "Identifying Author's Purpose",
            "lesson_code": "E6_Q1_0201",
        },
        "curriculum": {
            "competency_code": "EN6RC-Ia-2.2",
            "competency_description": "Identify the author's purpose for writing a text.",
            "sub_competencies": [
                {"id": "sc1", "label": "Identify purpose to entertain"}
            ],
        },
        "instructional_design": {
            "core_concept": "Authors write with a specific purpose.",
            "bloom_targets": [
                "Remember",
                "Understand",
                "Apply",
            ],
            "essential_question_seed": "Why does purpose matter?",
        },
        "optional": {
            "vocabulary_seeds": [],
            "topic_domains": {},
            "tone_register": "supportive",
            "length_preset": "standard",
        },
    }
    prompt_lab_request_payload = {
        "base_request": request_payload,
        "prompt_overrides": {
            "system_prompt_append": "Prefer concise reviewer-facing wording.",
            "section_overrides": {
                "intro": "Open with one short hook sentence.",
            },
        },
        "sample_case_id": "english_grade6_ph",
        "reviewer_label": "reviewer-a",
    }

    async def fake_blueprint(_request: Any) -> dict[str, Any]:
        return {"title": "Blueprint"}

    async def fake_workflow(ctx: Any, request: Any) -> Any:
        await ctx.run_node(
            SimpleNamespace(name="blueprint_node", _func=fake_blueprint), request
        )
        return GenerateResponse.model_validate(
            {
                "success": True,
                "pdf_base64": "cGRm",
                "preview": {"sections": []},
                "validation": {
                    "passed": True,
                    "failed_sections": [],
                    "failures": {},
                    "warnings": [],
                    "best_effort_sections": [],
                },
                "error": None,
            }
        )

    monkeypatch.setattr(fast_api_module.study_guide_workflow, "_func", fake_workflow)

    from fastapi.testclient import TestClient

    with TestClient(fast_api_module.app) as client:
        with client.stream("POST", "/generate", json=request_payload) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            lines = [line for line in response.iter_lines() if line]

    assert "event: progress" in lines
    assert any('"type": "node_started"' in line for line in lines)
    assert any('"node": "blueprint"' in line for line in lines)
    assert "event: result" in lines
    assert any('"success": true' in line for line in lines)

    with TestClient(fast_api_module.app) as client:
        with client.stream(
            "POST",
            "/prompt-lab/generate",
            json=prompt_lab_request_payload,
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            prompt_lab_lines = [line for line in response.iter_lines() if line]

    assert "event: progress" in prompt_lab_lines
    assert any('"type": "node_started"' in line for line in prompt_lab_lines)
    assert any('"node": "blueprint"' in line for line in prompt_lab_lines)
    assert "event: result" in prompt_lab_lines
    assert any('"success": true' in line for line in prompt_lab_lines)


def test_prompt_lab_curated_sample_smoke_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_blueprint(_request: Any) -> dict[str, Any]:
        return {"title": "Blueprint"}

    async def fake_workflow(ctx: Any, request: Any) -> Any:
        await ctx.run_node(
            SimpleNamespace(name="blueprint_node", _func=fake_blueprint), request
        )
        return GenerateResponse.model_validate(
            {
                "success": True,
                "pdf_base64": "cGRm",
                "preview": {"sections": []},
                "validation": {
                    "passed": True,
                    "failed_sections": [],
                    "failures": {},
                    "warnings": [],
                    "best_effort_sections": [],
                },
                "error": None,
            }
        )

    monkeypatch.setattr(fast_api_module.study_guide_workflow, "_func", fake_workflow)

    from fastapi.testclient import TestClient

    with TestClient(fast_api_module.app) as client:
        catalog_response = client.get("/prompt-lab/samples")
        assert catalog_response.status_code == 200
        catalog_payload = catalog_response.json()
        assert isinstance(catalog_payload, list)
        assert len(catalog_payload) > 0

        sample_id = catalog_payload[0]["id"]
        sample_response = client.get(f"/prompt-lab/samples/{sample_id}")
        assert sample_response.status_code == 200
        sample_payload = sample_response.json()

        with client.stream(
            "POST",
            "/prompt-lab/generate",
            json={
                "base_request": sample_payload["request"],
                "sample_case_id": sample_id,
                "reviewer_label": "smoke-reviewer",
                "prompt_overrides": {
                    "system_prompt_append": "Prefer concise reviewer-facing wording.",
                    "section_overrides": {
                        "intro": "Open with one short hook sentence.",
                    },
                },
            },
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            lines = [line for line in response.iter_lines() if line]

    assert "event: progress" in lines
    assert any('"type": "node_started"' in line for line in lines)
    assert any('"node": "blueprint"' in line for line in lines)
    assert "event: result" in lines
    assert any('"success": true' in line for line in lines)
