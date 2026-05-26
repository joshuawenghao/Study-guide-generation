"""Runtime prompt helpers for default and prompt-lab generation flows."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.prompts.system_prompt import build_system_prompt
from app.types import (
    Blueprint,
    GenerateRequest,
    PromptLabGenerateRequest,
    PromptLabSectionKey,
    StudyGuideRequest,
)


def resolve_base_request(request: StudyGuideRequest) -> GenerateRequest:
    if isinstance(request, PromptLabGenerateRequest):
        return request.base_request
    return request


def _section_override_for(request: StudyGuideRequest, section_key: str) -> str | None:
    if not isinstance(request, PromptLabGenerateRequest):
        return None

    try:
        prompt_lab_section_key = PromptLabSectionKey(section_key)
    except ValueError:
        return None

    override = request.prompt_overrides.section_overrides.get(prompt_lab_section_key)
    if override is None:
        return None

    cleaned_override = override.strip()
    return cleaned_override or None


def build_runtime_system_prompt(request: StudyGuideRequest) -> str:
    base_request = resolve_base_request(request)
    system_prompt = build_system_prompt(base_request)

    if not isinstance(request, PromptLabGenerateRequest):
        return system_prompt

    extra_guidance = request.prompt_overrides.system_prompt_append
    if extra_guidance is None:
        return system_prompt

    cleaned_guidance = extra_guidance.strip()
    if not cleaned_guidance:
        return system_prompt

    return (
        f"{system_prompt}\n\n"
        "Prompt-lab reviewer guidance: Apply the additional instructions below "
        "while still following the required schema and output constraints.\n"
        f"{cleaned_guidance}"
    )


def build_runtime_section_prompt(
    *,
    request: StudyGuideRequest,
    blueprint: Blueprint,
    prompt_builder: Callable[[Any, Blueprint, GenerateRequest], str],
    context_label: str,
    spec: Any = None,
) -> str:
    base_request = resolve_base_request(request)
    user_prompt = prompt_builder(spec, blueprint, base_request)

    override = _section_override_for(request, context_label)
    if override is None:
        return user_prompt

    return (
        f"{user_prompt}\n\n"
        "Prompt-lab reviewer override for this section: Follow the additional "
        "instructions below while preserving the existing JSON schema and all "
        "other output constraints.\n"
        f"{override}"
    )
