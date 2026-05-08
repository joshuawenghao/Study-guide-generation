"""Answer key section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.base import TEMP_ANSWER_KEY, call_gemini
from app.nodes.sections import _parse_section_response
from app.prompts.system_prompt import build_system_prompt
from app.prompts.templates.answer_key import build_prompt as build_answer_key_prompt
from app.types import Blueprint, GenerateRequest


async def generate_answer_key(
    request: GenerateRequest,
    blueprint: Blueprint,
    check_in: dict[str, Any],
    assessment_passage: dict[str, Any],
    assessment_questions: dict[str, Any],
) -> dict[str, Any]:
    system_prompt = build_system_prompt(request)
    user_prompt = build_answer_key_prompt(
        {
            "check_in": check_in,
            "assessment_passage": assessment_passage,
            "assessment_questions": assessment_questions,
        },
        blueprint,
        request,
    )
    response_text = await call_gemini(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=TEMP_ANSWER_KEY,
        context_label="answer_key",
    )
    return _parse_section_response(response_text, "answer_key")


answer_key_node = cast(
    Callable[
        [GenerateRequest, Blueprint, dict[str, Any], dict[str, Any], dict[str, Any]],
        Any,
    ],
    node(generate_answer_key),
)
