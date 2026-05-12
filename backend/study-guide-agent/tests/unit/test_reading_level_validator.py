from __future__ import annotations

from app.types import IntroSection
from app.validators.soft import reading_level as reading_level_module


def test_validate_reading_level_ignores_sections_within_target_band(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module.textstat,
        "flesch_kincaid_grade",
        lambda _text: 6.8,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=6,
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Think about how authors choose details.",
                essential_question="Why does author purpose matter?",
                paragraphs=["Authors choose details to guide the reader clearly."],
                bridge_to_lesson="You will study those choices today.",
            )
        },
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}
    assert result.warnings == []


def test_validate_reading_level_warns_for_section_outside_target_band(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module.textstat,
        "flesch_kincaid_grade",
        lambda _text: 9.4,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=6,
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Think about how authors choose details.",
                essential_question="Why does author purpose matter?",
                paragraphs=[
                    "Authors sometimes construct elaborately layered explanations that increase sentence complexity."
                ],
                bridge_to_lesson="You will study those choices today.",
            )
        },
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}
    assert any("intro" in warning for warning in result.warnings)
    assert any("9.4" in warning for warning in result.warnings)
