"""Learning targets section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.learning_targets import (
    build_prompt as build_learning_targets_prompt,
)
from app.types import Blueprint, StudyGuideRequest


async def generate_learning_targets(
    request: StudyGuideRequest, blueprint: Blueprint
) -> dict[str, Any]:
    return await generate_section(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_learning_targets_prompt,
        context_label="learning_targets",
    )


learning_targets_node = cast(
    Callable[[StudyGuideRequest, Blueprint], Any], node(generate_learning_targets)
)
