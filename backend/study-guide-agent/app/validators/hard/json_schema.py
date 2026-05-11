"""Hard validator for section payload schema conformance."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.types import SECTION_PAYLOAD_MODELS, ValidationResult


def _success_result() -> ValidationResult:
    return ValidationResult(
        passed=True,
        failed_sections=[],
        failures={},
        warnings=[],
        best_effort_sections=[],
    )


def _failure_result(section_key: str, messages: list[str]) -> ValidationResult:
    return ValidationResult(
        passed=False,
        failed_sections=[section_key],
        failures={section_key: messages},
        warnings=[],
        best_effort_sections=[],
    )


def validate_json_schema(*, section_key: str, payload: Any) -> ValidationResult:
    """Validate a generated section payload against its expected Pydantic model."""

    model_class = SECTION_PAYLOAD_MODELS.get(section_key)
    if model_class is None:
        return _failure_result(
            section_key,
            [f"No schema model is registered for section '{section_key}'."],
        )

    try:
        model_class.model_validate(payload)
    except ValidationError as error:
        return _failure_result(
            section_key,
            [
                f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}"
                for issue in error.errors()
            ],
        )

    return _success_result()
