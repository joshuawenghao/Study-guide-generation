"""Deep dive section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.deep_dive import build_prompt as build_deep_dive_prompt
from app.types import Blueprint, StudyGuideRequest


async def generate_deep_dive(
    request: StudyGuideRequest, blueprint: Blueprint
) -> dict[str, Any]:
    return await generate_section(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_deep_dive_prompt,
        context_label="deep_dive",
    )


deep_dive_node = cast(
    Callable[[StudyGuideRequest, Blueprint], Any], node(generate_deep_dive)
)
