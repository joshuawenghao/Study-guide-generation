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

from typing import Any, cast

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.workflow import Workflow

from app.agent import root_agent
from app.types import GenerateRequest, GenerateResponse


def test_root_workflow_is_constructible() -> None:
    """Integration smoke test for the configured workflow entrypoint."""

    session_service = InMemorySessionService()

    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(
        agent=cast(Any, root_agent),
        session_service=session_service,
        app_name="test",
    )

    assert session.id
    assert runner is not None
    assert isinstance(root_agent, Workflow)
    assert root_agent.name == "study_guide_generator"
    assert root_agent.input_schema is GenerateRequest
    assert root_agent.output_schema is GenerateResponse
