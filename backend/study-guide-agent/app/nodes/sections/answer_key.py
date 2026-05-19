"""Answer key section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

import re
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

QUOTED_PHRASE_PATTERN = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')


def _extract_quoted_phrases(value: str) -> list[str]:
    phrases: list[str] = []
    for straight_quote, curly_quote in QUOTED_PHRASE_PATTERN.findall(value):
        phrase = straight_quote or curly_quote
        if phrase:
            phrases.append(phrase)
    return phrases


def _normalize_evidence_quote(value: str) -> str:
    quoted_phrases = _extract_quoted_phrases(value)
    if quoted_phrases:
        return quoted_phrases[0]
    return value.strip()


def _normalize_assessment_answer_quotes(
    answer_key: dict[str, Any], assessment_passage: dict[str, Any]
) -> dict[str, Any]:
    passage_text = "\n".join(assessment_passage.get("passage", []))
    normalized_answers: list[dict[str, Any]] = []

    for raw_answer in answer_key.get("assessment_answers", []):
        answer = dict(raw_answer)
        possible_answer = str(answer.get("possible_answer", "")).strip()
        evidence_quote = str(answer.get("evidence_quote", "")).strip()
        normalized_evidence_quote = _normalize_evidence_quote(evidence_quote)
        quoted_phrases = _extract_quoted_phrases(possible_answer)

        if (
            quoted_phrases
            or not evidence_quote
            or not normalized_evidence_quote
            or normalized_evidence_quote not in passage_text
        ):
            normalized_answers.append(answer)
            continue

        separator = " " if possible_answer else ""
        answer["possible_answer"] = (
            f"{possible_answer}{separator}Evidence from the passage: {evidence_quote}."
        ).strip()
        normalized_answers.append(answer)

    return {
        **answer_key,
        "assessment_answers": normalized_answers,
    }


async def generate_answer_key(
    request: GenerateRequest,
    blueprint: Blueprint,
    check_in: dict[str, Any],
    assessment_passage: dict[str, Any],
    assessment_questions: dict[str, Any],
    step_up: dict[str, Any],
) -> dict[str, Any]:
    system_prompt = build_system_prompt(request)
    user_prompt = build_answer_key_prompt(
        {
            "check_in": check_in,
            "assessment_passage": assessment_passage,
            "assessment_questions": assessment_questions,
            "step_up": step_up,
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
    parsed_response = _parse_section_response(response_text, "answer_key")
    return _normalize_assessment_answer_quotes(parsed_response, assessment_passage)


answer_key_node = cast(
    Callable[
        [
            GenerateRequest,
            Blueprint,
            dict[str, Any],
            dict[str, Any],
            dict[str, Any],
            dict[str, Any],
        ],
        Any,
    ],
    node(generate_answer_key),
)
