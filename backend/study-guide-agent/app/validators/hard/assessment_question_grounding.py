"""Hard validator for grounding assessment-question evidence hints to the passage."""

from __future__ import annotations

import re

from app.types import (
    AssessmentPassageSection,
    AssessmentQuestionsSection,
    ValidationResult,
)

QUOTED_PHRASE_PATTERN = re.compile(r'"([^"\n]+)"|“([^”\n]+)”')
LOCATION_HINT_WORDS = {
    "paragraph",
    "sentence",
    "line",
    "opening",
    "beginning",
    "middle",
    "end",
    "final",
    "first",
    "second",
    "third",
    "last",
    "article",
    "passage",
    "text",
}
QUESTION_ALIGNMENT_WORDS = {
    "search",
    "think",
    "about",
    "specific",
    "term",
    "means",
    "meaning",
    "trying",
    "whether",
}
PURPOSE_HINT_WORDS = {
    "author",
    "purpose",
    "entertain",
    "inform",
    "persuade",
}
GENERIC_HINT_WORDS = {
    "the",
    "a",
    "an",
    "look",
    "for",
    "at",
    "to",
    "of",
    "in",
    "on",
    "part",
    "phrase",
    "detail",
    "details",
    "sentence",
    "paragraph",
    "line",
    "passage",
    "article",
    "text",
    "where",
    "that",
    "this",
    "best",
    "reveals",
    "shows",
    "show",
    "explains",
    "explain",
    "supports",
    "support",
    "search",
    "think",
    "about",
    "specific",
}


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


def _content_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[A-Za-z0-9']+", value.lower())
        if token and token not in GENERIC_HINT_WORDS
    }


def _looks_like_location_hint(value: str) -> bool:
    tokens = set(re.findall(r"[A-Za-z0-9']+", value.lower()))
    return bool(tokens & LOCATION_HINT_WORDS)


def _question_alignment_score(evidence_hint: str, question_text: str) -> float:
    hint_tokens = _content_tokens(evidence_hint) - QUESTION_ALIGNMENT_WORDS
    question_tokens = _content_tokens(question_text)
    if not hint_tokens or not question_tokens:
        return 0.0
    return len(hint_tokens & question_tokens) / len(hint_tokens | question_tokens)


def _passage_alignment_score(evidence_hint: str, passage_text: str) -> float:
    hint_tokens = _content_tokens(evidence_hint) - QUESTION_ALIGNMENT_WORDS
    passage_tokens = _content_tokens(passage_text)
    if not hint_tokens or not passage_tokens:
        return 0.0
    return len(hint_tokens & passage_tokens) / len(hint_tokens | passage_tokens)


def _looks_like_purpose_hint(value: str) -> bool:
    tokens = set(re.findall(r"[A-Za-z0-9']+", value.lower()))
    return bool(tokens & PURPOSE_HINT_WORDS)


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
                _token_overlap_score(
                    f"{question.question} {evidence_hint}",
                    target,
                ),
            )

        if best_score < 0.25 and _looks_like_location_hint(evidence_hint):
            supporting_tokens = (
                _content_tokens(question.question)
                | _content_tokens(" ".join(grounding_targets))
                | _content_tokens(passage_text)
            )
            hint_tokens = _content_tokens(evidence_hint)
            if hint_tokens:
                location_overlap = len(hint_tokens & supporting_tokens) / len(
                    hint_tokens
                )
                if location_overlap >= 0.25:
                    continue

        question_alignment = _question_alignment_score(
            evidence_hint,
            question.question,
        )
        passage_alignment = _passage_alignment_score(evidence_hint, passage_text)

        if (
            best_score < 0.25
            and _looks_like_location_hint(evidence_hint)
            and question_alignment >= 0.3
        ):
            continue

        if (
            best_score < 0.25
            and _looks_like_purpose_hint(evidence_hint)
            and question_alignment >= 0.3
            and passage_alignment >= 0.1
        ):
            continue

        if best_score < 0.25:
            failures.append(
                f"Assessment question {question.number} evidence_hint does not point to evidence that appears in the assessment passage: {evidence_hint}."
            )

    if failures:
        return _failure_result(failures)

    return _success_result()
