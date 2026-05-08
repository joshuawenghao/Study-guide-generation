"""Shared helpers for study guide section nodes."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from app.nodes.base import TEMP_SECTION, call_gemini
from app.prompts.system_prompt import build_system_prompt
from app.types import Blueprint, GenerateRequest


def _parse_section_response(response_text: str, context_label: str) -> dict[str, Any]:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Failed to parse {context_label} response as JSON. "
            f"Raw response:\n{response_text}"
        ) from error

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Failed to validate {context_label} response as a JSON object. "
            f"Raw response:\n{response_text}"
        )

    return payload


async def generate_section(
    *,
    request: GenerateRequest,
    blueprint: Blueprint,
    prompt_builder: Callable[[Any, Blueprint, GenerateRequest], str],
    context_label: str,
) -> dict[str, Any]:
    system_prompt = build_system_prompt(request)
    user_prompt = prompt_builder(None, blueprint, request)
    response_text = await call_gemini(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=TEMP_SECTION,
        context_label=context_label,
    )
    return _parse_section_response(response_text, context_label)
