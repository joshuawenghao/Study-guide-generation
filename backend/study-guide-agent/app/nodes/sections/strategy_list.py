"""Strategy list section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.strategy_list import (
    build_prompt as build_strategy_list_prompt,
)
from app.types import Blueprint, GenerateRequest


async def generate_strategy_list(
    request: GenerateRequest, blueprint: Blueprint
) -> dict[str, Any]:
    return await generate_section(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_strategy_list_prompt,
        context_label="strategy_list",
    )


strategy_list_node = cast(
    Callable[[GenerateRequest, Blueprint], Any], node(generate_strategy_list)
)
