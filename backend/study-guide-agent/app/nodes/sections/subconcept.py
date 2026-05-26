"""Subconcept section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.subconcept import build_prompt as build_subconcept_prompt
from app.types import Blueprint, StudyGuideRequest, SubCompetency


async def generate_subconcept(
    request: StudyGuideRequest,
    blueprint: Blueprint,
    sub_competency: SubCompetency,
) -> dict[str, Any]:
    return await generate_section(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_subconcept_prompt,
        context_label="subconcept",
        spec=sub_competency,
    )


subconcept_node = cast(
    Callable[[StudyGuideRequest, Blueprint, SubCompetency], Any],
    node(generate_subconcept),
)
