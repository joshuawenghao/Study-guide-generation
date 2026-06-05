"""Assessment questions section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.assessment_questions import (
    build_prompt as build_assessment_questions_prompt,
)
from app.types import Blueprint, StudyGuideRequest

SHORT_ANSWER_RESPONSE_TYPES = {
    "short_response",
    "short answer",
    "short_answer",
    "short-response",
    "text",
    "sentence",
    "one sentence",
    "one-sentence explanation",
}
MULTIPLE_CHOICE_RESPONSE_TYPES = {
    "multiple_choice",
    "multiple choice",
    "multiple-choice",
    "mcq",
}
PARAGRAPH_RESPONSE_TYPES = {
    "paragraph",
    "paragraph response",
    "paragraph_response",
    "extended response",
    "extended_response",
}


def _question_has_choice_markers(question_text: str) -> bool:
    return bool(
        re.search(r"\b[A-D][\).]\s", question_text)
        or re.search(r"\([A-D]\)", question_text)
        or "option" in question_text.casefold()
    )


def _question_prefers_short_answer(question_text: str) -> bool:
    normalized_question = question_text.casefold()
    return (
        normalized_question.startswith(
            ("what ", "how ", "why ", "explain ", "describe ")
        )
        or "author's purpose" in normalized_question
        or "authors purpose" in normalized_question
        or "primary purpose" in normalized_question
    )


def _normalize_expected_response_type(question_text: str, question_type: str) -> str:
    normalized_type = question_type.casefold()

    if normalized_type in MULTIPLE_CHOICE_RESPONSE_TYPES:
        if _question_has_choice_markers(
            question_text
        ) and not _question_prefers_short_answer(question_text):
            return "Multiple choice"
        return "Short answer"

    if normalized_type in PARAGRAPH_RESPONSE_TYPES:
        return "Paragraph response"

    if normalized_type in SHORT_ANSWER_RESPONSE_TYPES:
        return "Short answer"

    if normalized_type:
        return normalized_type.replace("_", " ").strip().title()

    if _question_prefers_short_answer(question_text) or _question_has_choice_markers(
        question_text
    ):
        return "Short answer"
    return "Short answer"


def _normalize_evidence_hint(
    *,
    question_text: str,
    raw_hint: str,
    focus_hint: str | None,
) -> str:
    normalized_hint = raw_hint.strip().strip('"')
    if normalized_hint:
        return normalized_hint

    if focus_hint:
        return f"Look for the part of the passage about {focus_hint}."

    normalized_question = question_text.casefold()
    if (
        "author's purpose" in normalized_question
        or "authors purpose" in normalized_question
    ):
        return "Look for the phrase that best reveals the author's purpose."
    return "Look for the specific detail in the passage that best supports your answer."


def normalize_assessment_questions_payload(
    assessment_questions: dict[str, Any],
    assessment_passage: dict[str, Any],
) -> dict[str, Any]:
    evidence_clues = [
        str(item).strip().strip('"')
        for item in assessment_passage.get("evidence_clues", [])
        if str(item).strip().strip('"')
    ]
    normalized_questions: list[dict[str, Any]] = []

    for index, raw_question in enumerate(assessment_questions.get("questions", [])):
        question = dict(raw_question)
        question_text = str(question.get("question", "")).strip()
        question_type = (
            str(
                question.get(
                    "expected_response_type",
                    question.get("question_type", "short_response"),
                )
            ).strip()
            or "short_response"
        )
        raw_hint = str(
            question.get(
                "evidence_hint",
                question.get("evidence_requirement", ""),
            )
        ).strip()
        focus_hint = evidence_clues[index] if index < len(evidence_clues) else None

        normalized_questions.append(
            {
                "number": question.get("number", index + 1),
                "question": question_text,
                "evidence_hint": _normalize_evidence_hint(
                    question_text=question_text,
                    raw_hint=raw_hint,
                    focus_hint=focus_hint,
                ),
                "expected_response_type": _normalize_expected_response_type(
                    question_text,
                    question_type,
                ),
            }
        )

    if not normalized_questions:
        return assessment_questions

    return {
        **assessment_questions,
        "questions": normalized_questions,
    }


async def generate_assessment_questions(
    request: StudyGuideRequest,
    blueprint: Blueprint,
    assessment_passage: dict[str, Any],
) -> dict[str, Any]:
    parsed_response = await generate_section(
        request=request,
        blueprint=blueprint,
        prompt_builder=build_assessment_questions_prompt,
        context_label="assessment_questions",
        spec=assessment_passage,
    )
    return normalize_assessment_questions_payload(parsed_response, assessment_passage)


assessment_questions_node = cast(
    Callable[[StudyGuideRequest, Blueprint, dict[str, Any]], Any],
    node(generate_assessment_questions),
)
