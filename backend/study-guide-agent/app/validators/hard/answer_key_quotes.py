"""Hard validator for assessment answer quotes against the assessment passage."""

from __future__ import annotations

import re

from app.types import AnswerKeySection, AssessmentPassageSection, ValidationResult

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
        failed_sections=["answer_key"],
        failures={"answer_key": messages},
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


def validate_answer_key_quotes(
    *,
    answer_key: AnswerKeySection,
    assessment_passage: AssessmentPassageSection,
) -> ValidationResult:
    """Validate quoted assessment-answer evidence against the assessment passage."""

    passage_text = "\n".join(assessment_passage.passage)
    failures: list[str] = []

    for answer in answer_key.assessment_answers:
        quoted_phrases = _extract_quoted_phrases(answer.possible_answer)
        if not quoted_phrases:
            failures.append(
                f"Assessment question {answer.question_number} must include at least one quoted phrase in possible_answer."
            )
            continue

        matching_phrase = next(
            (phrase for phrase in quoted_phrases if phrase in passage_text),
            None,
        )
        if matching_phrase is None:
            failures.append(
                f"Assessment question {answer.question_number} includes quoted phrase(s) that do not appear verbatim in the assessment passage: {', '.join(quoted_phrases)}."
            )

    if failures:
        return _failure_result(failures)

    return _success_result()
