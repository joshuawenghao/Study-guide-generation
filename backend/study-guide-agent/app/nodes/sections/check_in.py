"""Check-in section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.check_in import build_prompt as build_check_in_prompt
from app.types import Blueprint, StudyGuideRequest


async def generate_check_in(
    request: StudyGuideRequest,
    blueprint: Blueprint,
    model_passage: dict[str, Any],
) -> dict[str, Any]:
    return await generate_section(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_check_in_prompt,
        context_label="check_in",
        spec=model_passage,
    )


check_in_node = cast(
    Callable[[StudyGuideRequest, Blueprint, dict[str, Any]], Any],
    node(generate_check_in),
)
