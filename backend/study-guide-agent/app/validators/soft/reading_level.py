"""Soft validator for section reading-level drift from the target grade band."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel
from textstat import textstat

from app.types import ValidationResult


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


def validate_reading_level(
    *,
    target_grade_level: int,
    section_payloads: Mapping[str, Any],
) -> ValidationResult:
    """Warn when a section's reading level falls materially outside the target band."""

    warnings: list[str] = []
    for section_key, payload in section_payloads.items():
        section_text = "\n".join(_iter_text_fragments(payload)).strip()
        if not section_text:
            continue

        grade_score = float(textstat.flesch_kincaid_grade(section_text))
        if abs(grade_score - target_grade_level) <= 1.0:
            continue

        warnings.append(
            f"Reading level warning for {section_key}: Flesch-Kincaid grade {grade_score:.1f} is outside the target grade band for Grade {target_grade_level}."
        )

    return _success_result(warnings)
