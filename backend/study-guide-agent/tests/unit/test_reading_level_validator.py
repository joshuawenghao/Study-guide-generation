from __future__ import annotations

from app.types import IntroSection
from app.validators.soft import reading_level as reading_level_module


def test_validate_reading_level_ignores_sections_within_target_band(
    monkeypatch,
) -> None:
    monkeypatch.setattr(reading_level_module, "_has_local_cmudict", lambda: True)
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
    monkeypatch.setattr(reading_level_module, "_has_local_cmudict", lambda: True)
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


def test_validate_reading_level_warns_when_dependency_data_is_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(reading_level_module, "_has_local_cmudict", lambda: False)
    monkeypatch.setattr(
        reading_level_module,
        "_estimate_flesch_kincaid_grade_without_cmudict",
        lambda _text: 8.2,
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
    assert any("intro" in warning for warning in result.warnings)
    assert any("8.2" in warning for warning in result.warnings)


def test_validate_reading_level_skips_answer_key_section(monkeypatch) -> None:
    def fail_if_called(_text: str) -> float:
        raise AssertionError("answer_key should be skipped")

    monkeypatch.setattr(reading_level_module, "_has_local_cmudict", lambda: True)
    monkeypatch.setattr(
        reading_level_module.textstat,
        "flesch_kincaid_grade",
        fail_if_called,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=6,
        section_payloads={
            "answer_key": {
                "title": "Answer Key",
                "teacher_note": "Accept equivalent answers with evidence.",
                "assessment_answers": [],
            }
        },
    )

    assert result.passed is True
    assert result.warnings == []


def test_validate_reading_level_excludes_metadata_fields_from_scoring(
    monkeypatch,
) -> None:
    captured_texts: list[str] = []

    def capture_text(text: str) -> float:
        captured_texts.append(text)
        return 6.0

    monkeypatch.setattr(reading_level_module, "_has_local_cmudict", lambda: True)
    monkeypatch.setattr(
        reading_level_module.textstat,
        "flesch_kincaid_grade",
        capture_text,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=6,
        section_payloads={
            "subconcept": {
                "title": "Subconcept One",
                "sub_competency_id": "sc-1",
                "sub_competency_label": "Purpose clues",
                "explanation": "Clues in a text reveal purpose.",
            }
        },
    )

    assert result.passed is True
    assert result.warnings == []
    assert captured_texts == ["Purpose clues\nClues in a text reveal purpose."]
