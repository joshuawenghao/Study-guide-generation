"""Hard validator for self-assessment alignment with blueprint learning targets."""

from __future__ import annotations

from app.types import Blueprint, SelfAssessmentSection, ValidationResult


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
        failed_sections=["self_assessment"],
        failures={"self_assessment": messages},
        warnings=[],
        best_effort_sections=[],
    )


def validate_self_assess_targets(
    *,
    blueprint: Blueprint,
    self_assessment: SelfAssessmentSection,
) -> ValidationResult:
    """Validate that each self-assessment skill matches a blueprint objective verbatim."""

    valid_objectives = {target.objective for target in blueprint.learning_targets}
    mismatched_skills = [
        row.skill for row in self_assessment.rows if row.skill not in valid_objectives
    ]
    if not mismatched_skills:
        return _success_result()

    objective_list = "; ".join(
        target.objective for target in blueprint.learning_targets
    )
    return _failure_result(
        [
            "Self-assessment skills must match blueprint learning target objectives "
            f"verbatim. Mismatched skills: {', '.join(mismatched_skills)}. "
            f"Allowed objectives: {objective_list}."
        ]
    )
