"""Assessment questions section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.assessment_questions import (
    build_prompt as build_assessment_questions_prompt,
)
from app.types import Blueprint, GenerateRequest


async def generate_assessment_questions(
    request: GenerateRequest,
    blueprint: Blueprint,
    assessment_passage: dict[str, Any],
) -> dict[str, Any]:
    return await generate_section(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_assessment_questions_prompt,
        context_label="assessment_questions",
        spec=assessment_passage,
    )


assessment_questions_node = cast(
    Callable[[GenerateRequest, Blueprint, dict[str, Any]], Any],
    node(generate_assessment_questions),
)
