"""Hard validator for distinct model and assessment passage domains."""

from __future__ import annotations

from app.types import Blueprint, ValidationResult


def _success_result() -> ValidationResult:
    return ValidationResult(
        passed=True,
        failed_sections=[],
        failures={},
        warnings=[],
        best_effort_sections=[],
    )


def _failure_result(message: str) -> ValidationResult:
    return ValidationResult(
        passed=False,
        failed_sections=["assessment_passage"],
        failures={"assessment_passage": [message]},
        warnings=[],
        best_effort_sections=[],
    )


def validate_passage_domain_diff(*, blueprint: Blueprint) -> ValidationResult:
    """Validate that model and assessment passage domains differ."""

    model_domain = blueprint.topic_domains.model_passage.strip()
    assessment_domain = blueprint.topic_domains.assessment_passage.strip()

    if not model_domain or not assessment_domain:
        return _failure_result(
            "Model and assessment passage topic domains must both be present for domain-difference validation."
        )

    if model_domain.casefold() == assessment_domain.casefold():
        return _failure_result(
            "Assessment passage topic domain must differ from the model passage topic domain. "
            f"Both are '{assessment_domain}'."
        )

    return _success_result()
