"""Blueprint generation node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node
from pydantic import ValidationError

from app.nodes.base import TEMP_BLUEPRINT, call_gemini
from app.prompts.runtime import build_runtime_system_prompt, resolve_base_request
from app.prompts.templates.blueprint import build_prompt as build_blueprint_prompt
from app.types import Blueprint, StudyGuideRequest


def _parse_blueprint_response(response_text: str) -> Blueprint:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Failed to parse blueprint response as JSON. "
            f"Raw response:\n{response_text}"
        ) from error

    try:
        return Blueprint.model_validate(payload)
    except ValidationError as error:
        raise RuntimeError(
            "Failed to validate blueprint response against the Blueprint schema. "
            f"Raw response:\n{response_text}"
        ) from error


async def generate_blueprint(request: StudyGuideRequest) -> Blueprint:
    base_request = resolve_base_request(request)
    system_prompt = build_runtime_system_prompt(request)
    user_prompt = build_blueprint_prompt(
        spec=None,
        blueprint=None,
        request=base_request,
    )
    response_text = await call_gemini(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=TEMP_BLUEPRINT,
        context_label="blueprint",
    )
    return _parse_blueprint_response(response_text)


blueprint_node = cast(Callable[[StudyGuideRequest], Any], node(generate_blueprint))
