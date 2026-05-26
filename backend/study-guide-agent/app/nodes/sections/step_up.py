"""Step-up section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.step_up import build_prompt as build_step_up_prompt
from app.types import Blueprint, StudyGuideRequest


async def generate_step_up(
    request: StudyGuideRequest,
    blueprint: Blueprint,
    assessment_passage: dict[str, Any],
    assessment_questions: dict[str, Any],
) -> dict[str, Any]:
    return await generate_section(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_step_up_prompt,
        context_label="step_up",
        spec={
            "assessment_passage": assessment_passage,
            "assessment_questions": assessment_questions,
        },
    )


step_up_node = cast(
    Callable[[StudyGuideRequest, Blueprint, dict[str, Any], dict[str, Any]], Any],
    node(generate_step_up),
)
