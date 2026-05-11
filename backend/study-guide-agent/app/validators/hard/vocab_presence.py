"""Hard validator for blueprint vocabulary coverage across body sections."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from app.types import Blueprint, ValidationResult

EXCLUDED_SECTION_KEYS = {"answer_key", "blueprint", "vocabulary"}


def _success_result() -> ValidationResult:
    return ValidationResult(
        passed=True,
        failed_sections=[],
        failures={},
        warnings=[],
        best_effort_sections=[],
    )


def _failure_result(section_keys: list[str], messages: list[str]) -> ValidationResult:
    failure_keys = section_keys or ["intro"]
    return ValidationResult(
        passed=False,
        failed_sections=failure_keys,
        failures=dict.fromkeys(failure_keys, messages),
        warnings=[],
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


def _build_body_text(section_payloads: Mapping[str, Any]) -> tuple[list[str], str]:
    included_section_keys: list[str] = []
    text_fragments: list[str] = []

    for section_key, payload in section_payloads.items():
        if section_key in EXCLUDED_SECTION_KEYS:
            continue
        included_section_keys.append(section_key)
        text_fragments.extend(_iter_text_fragments(payload))

    return included_section_keys, "\n".join(text_fragments).casefold()


def validate_vocab_presence(
    *,
    blueprint: Blueprint,
    section_payloads: Mapping[str, Any],
) -> ValidationResult:
    """Validate that every blueprint vocabulary word appears in body sections."""

    body_section_keys, body_text = _build_body_text(section_payloads)
    if not body_section_keys:
        return _failure_result(
            [],
            [
                "No body sections were provided for vocabulary coverage validation.",
            ],
        )

    missing_words = [
        entry.word
        for entry in blueprint.vocabulary
        if entry.word.casefold() not in body_text
    ]
    if not missing_words:
        return _success_result()

    missing_words_display = ", ".join(sorted(missing_words, key=str.casefold))
    checked_sections_display = ", ".join(body_section_keys)
    return _failure_result(
        body_section_keys,
        [
            "Missing blueprint vocabulary words in body sections: "
            f"{missing_words_display}. Checked sections: {checked_sections_display}."
        ],
    )
