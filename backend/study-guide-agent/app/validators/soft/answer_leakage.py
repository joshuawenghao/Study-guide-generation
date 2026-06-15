"""Soft validator for answer leakage from answer-key evidence into body sections."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from app.types import AnswerKeySection, ValidationResult

EXCLUDED_SECTION_KEYS = {
    "answer_key",
    "assessment_passage",
    "assessment_questions",
    # Structurally disconnected from assessment content — leakage checks produce
    # false positives on these sections.
    "model_passage",
    "check_in",
    "learning_targets",
    "strategy_list",
    "self_assessment",
}
QUOTED_PHRASE_PATTERN = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')


def _success_result(warnings: list[str]) -> ValidationResult:
    return ValidationResult(
        passed=True,
        failed_sections=[],
        failures={},
        warnings=warnings,
        best_effort_sections=[],
    )


def _iter_text_fragments(value: Any) -> Iterable[str]:
    if isinstance(value, BaseModel):
        yield from _iter_text_fragments(value.model_dump())
        return

    if isinstance(value, str):
        yield value
        return

    if isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_text_fragments(item)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _iter_text_fragments(item)


MIN_PHRASE_WORD_COUNT = 5


def _extract_quoted_phrases(answer_key: AnswerKeySection) -> list[str]:
    phrases: list[str] = []
    for answer in answer_key.assessment_answers:
        for straight_quote, curly_quote in QUOTED_PHRASE_PATTERN.findall(
            answer.evidence_quote
        ):
            phrase = straight_quote or curly_quote
            if phrase and len(phrase.split()) >= MIN_PHRASE_WORD_COUNT:
                phrases.append(phrase)
    return phrases


def validate_answer_leakage(
    *,
    answer_key: AnswerKeySection,
    section_payloads: Mapping[str, Any],
) -> ValidationResult:
    """Warn when quoted answer-key evidence appears in body sections."""

    quoted_phrases = _extract_quoted_phrases(answer_key)
    if not quoted_phrases:
        return _success_result([])

    warnings: list[str] = []
    for section_key, payload in section_payloads.items():
        if section_key in EXCLUDED_SECTION_KEYS:
            continue

        section_text = "\n".join(_iter_text_fragments(payload)).casefold()
        leaked_phrases = sorted(
            {phrase for phrase in quoted_phrases if phrase.casefold() in section_text},
            key=str.casefold,
        )
        if leaked_phrases:
            warnings.append(
                f"Potential answer leakage in {section_key}: quoted answer-key phrase(s) also appear in this section: {', '.join(leaked_phrases)}."
            )

    return _success_result(warnings)
