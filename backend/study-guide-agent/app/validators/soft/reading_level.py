"""Soft validator for section reading-level drift from the target grade band."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import nltk
from pydantic import BaseModel
from textstat import textstat
from textstat.backend.utils._get_pyphen import get_pyphen

from app.types import ValidationResult

PROJECT_NLTK_DATA_DIR = Path(__file__).resolve().parents[3] / ".nltk_data"

PROSE_SECTION_KEYS = {
    "intro",
    "core_explainer",
    "subconcept",
    "deep_dive",
    "assessment_passage",
}
MIN_RELIABLE_WORD_COUNT = 30
FIELD_EXCLUSIONS = {
    "title",
    "teacher_note",
    "lesson_id",
    "number",
    "question_number",
    "sub_competency_id",
    "topic_domain",
    "genre",
    "part_of_speech",
    "passage_title",
    "expected_response_type",
    "evidence_hint",
    "estimated_minutes",
    "activity_type",
}

if PROJECT_NLTK_DATA_DIR.exists():
    project_nltk_path = str(PROJECT_NLTK_DATA_DIR)
    if project_nltk_path not in nltk.data.path:
        nltk.data.path.insert(0, project_nltk_path)


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
        for key, item in value.items():
            if str(key) in FIELD_EXCLUSIONS:
                continue
            yield from _iter_text_fragments(item)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _iter_text_fragments(item)


def _estimate_flesch_kincaid_grade_without_cmudict(text: str) -> float:
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)
    if not words:
        return 0.0

    sentences = re.findall(r"\b[^.!?]+[.!?]*", text, re.UNICODE)
    sentence_count = max(
        1,
        sum(
            1
            for sentence in sentences
            if len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", sentence)) > 2
        ),
    )

    pyphen = get_pyphen("en_US")
    syllable_count = sum(len(pyphen.positions(word.lower())) + 1 for word in words)

    average_sentence_length = len(words) / sentence_count
    average_syllables_per_word = syllable_count / len(words)
    return (
        (0.39 * average_sentence_length) + (11.8 * average_syllables_per_word) - 15.59
    )


def _count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text))


def _has_local_cmudict() -> bool:
    try:
        nltk.data.find("corpora/cmudict")
    except LookupError:
        return False
    return True


def _linsear_grade(text: str) -> float:
    """Grade level via Linsear Write formula, using the full section text.

    Linsear only counts words with 3+ syllables as hard, so two-syllable
    domain vocabulary (e.g. 'treaty', 'colony', 'fraction') does not inflate
    the score the way Flesch-Kincaid does.
    """
    return float(textstat.linsear_write_formula(text, strict_upper=False))


def _warning_tolerance(target_grade_level: int, section_key: str) -> float:
    if target_grade_level <= 4:
        tolerance = 1.5
    elif target_grade_level <= 6:
        tolerance = 1.25
    elif target_grade_level >= 11:
        tolerance = 1.5
    else:
        tolerance = 1.25

    if section_key == "intro" and target_grade_level <= 6:
        tolerance += 0.5

    if (
        section_key in {"model_passage", "assessment_passage"}
        and target_grade_level >= 9
    ):
        tolerance += 0.25

    return tolerance


def _low_warning_tolerance(target_grade_level: int, section_key: str) -> float:
    tolerance = _warning_tolerance(target_grade_level, section_key) + 1.0

    if target_grade_level >= 9:
        tolerance += 0.5

    if section_key in {"model_passage", "assessment_passage"}:
        tolerance += 0.5

    return tolerance


def validate_reading_level(
    *,
    target_grade_level: int,
    section_payloads: Mapping[str, Any],
) -> ValidationResult:
    """Warn when a section's reading level falls materially outside the target band."""

    warnings: list[str] = []
    for section_key, payload in section_payloads.items():
        if section_key not in PROSE_SECTION_KEYS:
            continue

        section_text = "\n".join(_iter_text_fragments(payload)).strip()
        if not section_text:
            continue
        if _count_words(section_text) < MIN_RELIABLE_WORD_COUNT:
            continue

        if not _has_local_cmudict():
            grade_score = _estimate_flesch_kincaid_grade_without_cmudict(section_text)
            metric_name = "Flesch-Kincaid"
        else:
            try:
                grade_score = _linsear_grade(section_text)
                metric_name = "Linsear Write"
            except LookupError:
                grade_score = _estimate_flesch_kincaid_grade_without_cmudict(
                    section_text
                )
                metric_name = "Flesch-Kincaid"
            except Exception as error:
                warnings.append(
                    "Reading level warning: reading-level analysis was skipped "
                    f"because the dependency data is unavailable ({error.__class__.__name__})."
                )
                break

        score_delta = grade_score - target_grade_level
        if score_delta > _warning_tolerance(target_grade_level, section_key):
            warnings.append(
                f"Reading level warning for {section_key}: {metric_name} grade {grade_score:.1f} is above the target grade band for Grade {target_grade_level}."
            )
            continue

        if score_delta < -_low_warning_tolerance(target_grade_level, section_key):
            warnings.append(
                f"Reading level warning for {section_key}: {metric_name} grade {grade_score:.1f} is below the target grade band for Grade {target_grade_level}."
            )

    return _success_result(warnings)
