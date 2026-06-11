"""Model passage section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.model_passage import (
    build_prompt as build_model_passage_prompt,
)
from app.types import Blueprint, StudyGuideRequest


async def generate_model_passage(
    request: StudyGuideRequest, blueprint: Blueprint
) -> dict[str, Any]:
    result = await generate_section(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_model_passage_prompt,
        context_label="model_passage",
    )
    # Gemini occasionally omits evidence_focus; fill in a safe default so schema
    # validation never fails on a missing field and the renderer always has the key.
    result.setdefault("evidence_focus", "")
    return result


model_passage_node = cast(
    Callable[[StudyGuideRequest, Blueprint], Any], node(generate_model_passage)
)
