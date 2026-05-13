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

import os

from fastapi import FastAPI

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.cli.fast_api import get_fast_api_app

from app.app_utils.telemetry import setup_telemetry

setup_telemetry()

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
