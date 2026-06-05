"""Assessment questions section node for the study guide workflow."""

# ruff: noqa: E402

from __future__ import annotations

import re
from collections.abc import Callable
from difflib import SequenceMatcher
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections import generate_section
from app.prompts.templates.assessment_questions import (
    build_prompt as build_assessment_questions_prompt,
)
from app.types import Blueprint, StudyGuideRequest

QUOTED_PHRASE_PATTERN = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')


def _extract_quoted_phrases(value: str) -> list[str]:
    phrases: list[str] = []
    for straight_quote, curly_quote in QUOTED_PHRASE_PATTERN.findall(value):
        phrase = straight_quote or curly_quote
        if phrase:
            phrases.append(phrase)
    return phrases


def _collect_quote_candidates(assessment_passage: dict[str, Any]) -> list[str]:
    passage_lines = [
        str(item).strip()
        for item in assessment_passage.get("passage", [])
        if str(item).strip()
    ]
    passage_text = "\n".join(passage_lines)

    candidates: list[str] = []
    for clue in assessment_passage.get("evidence_clues", []):
        normalized_clue = str(clue).strip().strip('"')
        if (
            normalized_clue
            and normalized_clue in passage_text
            and normalized_clue not in candidates
        ):
            candidates.append(normalized_clue)

    for paragraph in passage_lines:
        if paragraph and paragraph not in candidates:
            candidates.append(paragraph)

        for fragment in paragraph.replace(";", ",").split(","):
            normalized_fragment = fragment.strip()
            if (
                len(normalized_fragment.split()) >= 3
                and normalized_fragment in passage_text
                and normalized_fragment not in candidates
            ):
                candidates.append(normalized_fragment)

    return candidates


def _token_overlap_score(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[A-Za-z0-9']+", left.lower()))
    right_tokens = set(re.findall(r"[A-Za-z0-9']+", right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _best_matching_quote_candidate(
    targets: list[str], candidates: list[str]
) -> str | None:
    best_candidate: str | None = None
    best_score = 0.0

    for candidate in candidates:
        for target in targets:
            normalized_target = target.strip()
            if not normalized_target:
                continue
            score = max(
                SequenceMatcher(
                    None, candidate.lower(), normalized_target.lower()
                ).ratio(),
                _token_overlap_score(candidate, normalized_target),
            )
            if score > best_score:
                best_score = score
                best_candidate = candidate

    if best_score >= 0.35:
        return best_candidate
    return None


def _strip_nonverbatim_quotes(value: str, exact_quote: str | None) -> str:
    cleaned_value = value
    for phrase in _extract_quoted_phrases(value):
        if exact_quote is not None and phrase == exact_quote:
            continue
        cleaned_value = cleaned_value.replace(f'"{phrase}"', phrase).replace(
            f"“{phrase}”", phrase
        )
    return cleaned_value


def _normalize_answer_expectation(question_text: str, question_type: str) -> str:
    normalized_question = question_text.casefold()
    normalized_type = question_type.casefold()

    if (
        "author's purpose" in normalized_question
        or "authors purpose" in normalized_question
    ):
        return "State the author's purpose and explain how the passage supports it."
    if normalized_question.startswith("how ") or " how " in normalized_question:
        return "Explain how the passage details support your answer."
    if normalized_question.startswith("why ") or " why " in normalized_question:
        return "Explain why using details from the passage."
    if normalized_type == "multiple_choice":
        return "Choose the best answer and justify it with passage evidence."
    return "Answer the question clearly and support it with passage evidence."


def _collect_evidence_clues(assessment_passage: dict[str, Any]) -> list[str]:
    return [
        str(item).strip().strip('"')
        for item in assessment_passage.get("evidence_clues", [])
        if str(item).strip().strip('"')
    ]


def _normalize_evidence_requirement(
    *,
    question_text: str,
    focus_hint: str | None,
) -> str:
    if focus_hint:
        return f"Use one exact phrase from the part of the passage about {focus_hint}."

    normalized_question = question_text.casefold()
    if (
        "author's purpose" in normalized_question
        or "authors purpose" in normalized_question
    ):
        return "Use one exact phrase from the passage that best reveals the author's purpose."
    return "Use one exact phrase from the passage that best supports your answer."


def normalize_assessment_questions_payload(
    assessment_questions: dict[str, Any],
    assessment_passage: dict[str, Any],
) -> dict[str, Any]:
    evidence_clues = _collect_evidence_clues(assessment_passage)
    normalized_questions: list[dict[str, Any]] = []

    for index, raw_question in enumerate(assessment_questions.get("questions", [])):
        question = dict(raw_question)
        question_text = str(question.get("question", "")).strip()
        question_type = (
            str(question.get("question_type", "short_response")).strip()
            or "short_response"
        )
        answer_expectation = str(question.get("answer_expectation", "")).strip()
        evidence_requirement = str(question.get("evidence_requirement", "")).strip()

        focus_hint = _best_matching_quote_candidate(
            [question_text, answer_expectation, evidence_requirement],
            evidence_clues,
        )

        normalized_questions.append(
            {
                "number": question.get("number", index + 1),
                "question": question_text,
                "question_type": question_type,
                "answer_expectation": _normalize_answer_expectation(
                    question_text,
                    question_type,
                ),
                "evidence_requirement": _normalize_evidence_requirement(
                    question_text=question_text,
                    focus_hint=focus_hint,
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
