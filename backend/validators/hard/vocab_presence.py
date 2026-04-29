"""
Hard validator: vocab_presence

Rule: Every vocabulary word listed in the blueprint must appear —
case-insensitively — somewhere in the combined text of all body sections.

Body sections are every generated section except the vocabulary-definition
section itself and the answer key. Concretely: intro, learning_targets,
warmup, core_explainer, all subconcept blocks, strategy_list, deep_dive,
model_passage, check_in, key_points, assessment_passage,
assessment_questions, step_up, and self_assessment.

Match type: substring, case-insensitive.
Failure unit: one failure message per missing vocabulary word.
"""

from __future__ import annotations

from typing import Any

from backend.types import Blueprint


def _extract_text_from_value(value: Any) -> str:
    """
    Recursively extract all string leaf values from a JSON-compatible
    structure (dict, list, or scalar) and concatenate them with spaces.
    This ensures vocabulary words are matched regardless of which JSON
    field they appear in within a section output.
    """
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_extract_text_from_value(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_extract_text_from_value(item) for item in value)
    return ""


def check_vocab_presence(
    blueprint: Blueprint,
    body_sections: dict[str, Any],
) -> list[str]:
    """
    Hard validator — vocab_presence.

    Parameters
    ----------
    blueprint:
        The shared Blueprint object produced by blueprint_node. Its
        ``vocabulary`` list is the authoritative set of words to check.
    body_sections:
        A dict mapping section_key -> section output (dict or Pydantic
        model). Must include all body sections (all sections except the
        vocabulary-definition section itself and the answer key).

    Returns
    -------
    list[str]
        Failure messages, one per missing vocabulary word.
        An empty list means all vocabulary words are present.
    """
    combined_text = " ".join(
        _extract_text_from_value(section)
        for section in body_sections.values()
    ).lower()

    failures: list[str] = []
    for entry in blueprint.vocabulary:
        if entry.word.lower() not in combined_text:
            failures.append(
                f"Vocabulary word '{entry.word}' does not appear in any body section."
            )
    return failures
