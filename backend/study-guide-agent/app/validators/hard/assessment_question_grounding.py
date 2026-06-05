"""Hard validator for grounding assessment-question evidence hints to the passage."""

from __future__ import annotations

import re

from app.types import (
    AssessmentPassageSection,
    AssessmentQuestionsSection,
    ValidationResult,
)

QUOTED_PHRASE_PATTERN = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')


def _success_result() -> ValidationResult:
    return ValidationResult(
        passed=True,
        failed_sections=[],
        failures={},
        warnings=[],
        best_effort_sections=[],
    )


def _failure_result(messages: list[str]) -> ValidationResult:
    return ValidationResult(
        passed=False,
        failed_sections=["assessment_questions"],
        failures={"assessment_questions": messages},
        warnings=[],
        best_effort_sections=[],
    )


def _extract_quoted_phrases(value: str) -> list[str]:
    phrases: list[str] = []
    for straight_quote, curly_quote in QUOTED_PHRASE_PATTERN.findall(value):
        phrase = straight_quote or curly_quote
        if phrase:
            phrases.append(phrase)
    return phrases


def _token_overlap_score(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[A-Za-z0-9']+", left.lower()))
    right_tokens = set(re.findall(r"[A-Za-z0-9']+", right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def validate_assessment_question_grounding(
    *,
    assessment_questions: AssessmentQuestionsSection,
    assessment_passage: AssessmentPassageSection,
) -> ValidationResult:
    passage_text = "\n".join(assessment_passage.passage)
    evidence_clues = [
        clue for clue in assessment_passage.evidence_clues if clue.strip()
    ]
    grounding_targets = evidence_clues or list(assessment_passage.passage)
    failures: list[str] = []

    for question in assessment_questions.questions:
        evidence_hint = question.evidence_hint.strip()
        if not evidence_hint:
            failures.append(
                f"Assessment question {question.number} must include a non-empty evidence_hint grounded in the assessment passage."
            )
            continue

        quoted_phrases = _extract_quoted_phrases(evidence_hint)
        if quoted_phrases:
            matching_phrase = next(
                (phrase for phrase in quoted_phrases if phrase in passage_text),
                None,
            )
            if matching_phrase is None:
                failures.append(
                    f"Assessment question {question.number} evidence_hint includes quoted phrase(s) that do not appear verbatim in the assessment passage: {', '.join(quoted_phrases)}."
                )
            continue

        best_score = 0.0
        for target in grounding_targets:
            best_score = max(
                best_score,
                _token_overlap_score(evidence_hint, target),
            )

        if best_score < 0.25:
            failures.append(
                f"Assessment question {question.number} evidence_hint does not point to evidence that appears in the assessment passage: {evidence_hint}."
            )

    if failures:
        return _failure_result(failures)

    return _success_result()
