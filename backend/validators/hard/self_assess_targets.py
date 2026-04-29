"""
Hard validator: self_assess_targets

Rule: Each skill row in the self-assessment section must match exactly one
learning target objective from the blueprint — verbatim (exact string
equality, case-sensitive).

Failure unit: one failure message per skill row that does not match any
learning target objective verbatim.
"""

from __future__ import annotations

from backend.types import Blueprint, SelfAssessmentOutput


def check_self_assess_targets(
    blueprint: Blueprint,
    self_assessment: SelfAssessmentOutput,
) -> list[str]:
    """
    Hard validator — self_assess_targets.

    Parameters
    ----------
    blueprint:
        The shared Blueprint object. Its ``learning_targets`` list provides
        the set of valid objective strings.
    self_assessment:
        The parsed output of the self_assessment section node.

    Returns
    -------
    list[str]
        Failure messages, one per skill row whose text does not verbatim
        match any learning target objective.
        An empty list means all skills are valid.
    """
    valid_objectives: set[str] = {
        lt.objective for lt in blueprint.learning_targets
    }

    failures: list[str] = []
    for row in self_assessment.skills:
        if row.skill not in valid_objectives:
            failures.append(
                f"Self-assessment skill '{row.skill}' does not verbatim match "
                "any learning target objective in the blueprint."
            )
    return failures
