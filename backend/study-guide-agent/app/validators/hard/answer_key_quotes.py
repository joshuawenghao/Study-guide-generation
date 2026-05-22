"""Hard validator for assessment answer quotes against the assessment passage."""

from __future__ import annotations

import re

from app.types import (
    AnswerKeySection,
    AssessmentPassageSection,
    ModelPassageSection,
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
    model_passage: ModelPassageSection | None = None,
) -> ValidationResult:
    """Validate answer-key evidence quotes against their source passages."""

    passage_text = "\n".join(assessment_passage.passage)
    failures: list[str] = []

    if model_passage is not None:
        model_passage_text = "\n".join(model_passage.passage)
        for answer in answer_key.check_in_answers:
            normalized_quote = answer.evidence_quote.strip()
            if not normalized_quote or normalized_quote == "N/A":
                failures.append(
                    f"Check-in question {answer.question_number} must include an evidence_quote taken verbatim from the model passage."
                )
                continue

            extracted_quotes = _extract_quoted_phrases(normalized_quote)
            candidate_quotes = extracted_quotes or [normalized_quote]
            matching_quote = next(
                (phrase for phrase in candidate_quotes if phrase in model_passage_text),
                None,
            )
            if matching_quote is None:
                failures.append(
                    f"Check-in question {answer.question_number} includes an evidence_quote that does not appear verbatim in the model passage: {normalized_quote}."
                )

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
