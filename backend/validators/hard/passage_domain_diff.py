"""
Hard validator: passage_domain_diff

Rule: The topic domain assigned to the assessment passage must be different
from the topic domain assigned to the model passage. Identical domains
indicate a risk of answer leakage from the model passage into the assessment.

Comparison: exact string equality on blueprint.topic_domains values.
Failure unit: a single failure message naming both domains if they are equal.
"""

from __future__ import annotations

from backend.types import Blueprint


def check_passage_domain_diff(blueprint: Blueprint) -> list[str]:
    """
    Hard validator — passage_domain_diff.

    Parameters
    ----------
    blueprint:
        The shared Blueprint object. Its ``topic_domains`` sub-object carries
        the ``model_passage`` and ``assessment_passage`` domain strings that
        must differ.

    Returns
    -------
    list[str]
        A single-element list with a failure message if the two domains are
        identical, otherwise an empty list.
    """
    model_domain = blueprint.topic_domains.model_passage
    assessment_domain = blueprint.topic_domains.assessment_passage

    if model_domain == assessment_domain:
        return [
            f"Assessment passage domain '{assessment_domain}' is identical to "
            f"the model passage domain '{model_domain}'. The two domains must "
            "differ to prevent answer leakage."
        ]
    return []
