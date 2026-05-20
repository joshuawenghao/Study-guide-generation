"""Hard validator for grounding assessment-question evidence requirements to the passage."""

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


def validate_assessment_question_grounding(
    *,
    assessment_questions: AssessmentQuestionsSection,
    assessment_passage: AssessmentPassageSection,
) -> ValidationResult:
    passage_text = "\n".join(assessment_passage.passage)
    failures: list[str] = []

    for question in assessment_questions.questions:
        quoted_phrases = _extract_quoted_phrases(question.evidence_requirement)
        if not quoted_phrases:
            failures.append(
                f"Assessment question {question.number} evidence_requirement must include at least one exact quoted phrase from the assessment passage."
            )
            continue

        matching_phrase = next(
            (phrase for phrase in quoted_phrases if phrase in passage_text),
            None,
        )
        if matching_phrase is None:
            failures.append(
                f"Assessment question {question.number} evidence_requirement includes quoted phrase(s) that do not appear verbatim in the assessment passage: {', '.join(quoted_phrases)}."
            )

    if failures:
        return _failure_result(failures)

    return _success_result()
