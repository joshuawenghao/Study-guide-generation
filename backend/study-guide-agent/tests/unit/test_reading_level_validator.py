from __future__ import annotations

from app.types import IntroSection
from app.validators.soft import reading_level as reading_level_module


def test_validate_reading_level_ignores_sections_within_target_band(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 6.5,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=6,
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Think about how authors choose details.",
                essential_question="Why does author purpose matter?",
                paragraphs=[
                    "Authors choose details to guide the reader clearly. Readers can study those details, compare the clues, and explain the writer's purpose with confidence during class discussion and independent practice."
                ],
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
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 9.0,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=6,
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Think about how authors choose details.",
                essential_question="Why does author purpose matter?",
                paragraphs=[
                    "Authors sometimes construct elaborately layered explanations that increase sentence complexity and require readers to process several linked ideas before they can identify the writer's message or purpose in the passage."
                ],
                bridge_to_lesson="You will study those choices today.",
            )
        },
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}
    assert any("intro" in warning for warning in result.warnings)
    assert any("9.0" in warning for warning in result.warnings)
    assert any("above the target grade band" in warning for warning in result.warnings)
    assert any("Flesch-Kincaid" in warning for warning in result.warnings)


def test_validate_reading_level_warns_when_dependency_data_is_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: (_ for _ in ()).throw(RuntimeError("pyphen unavailable")),
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=6,
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Think about how authors choose details.",
                essential_question="Why does author purpose matter?",
                paragraphs=[
                    "Authors choose details to guide the reader clearly. Readers can study those details, compare the clues, and explain the writer's purpose with confidence during class discussion and independent practice."
                ],
                bridge_to_lesson="You will study those choices today.",
            )
        },
    )

    assert result.passed is True
    assert len(result.warnings) == 1
    assert "unavailable" in result.warnings[0]
    assert "RuntimeError" in result.warnings[0]


def test_validate_reading_level_skips_answer_key_section(monkeypatch) -> None:
    def fail_if_called(_text: str) -> float:
        raise AssertionError("answer_key should be skipped")

    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
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

    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        capture_text,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=6,
        section_payloads={
            "subconcept": {
                "title": "Subconcept One",
                "sub_competency_id": "sc-1",
                "sub_competency_label": "Purpose clues",
                "explanation": "Clues in a text reveal purpose. Students can look at word choice, tone, and details to decide whether the writer wants to entertain, inform, or persuade the reader.",
            }
        },
    )

    assert result.passed is True
    assert result.warnings == []
    assert captured_texts == [
        "Purpose clues\nClues in a text reveal purpose. Students can look at word choice, tone, and details to decide whether the writer wants to entertain, inform, or persuade the reader."
    ]


def test_validate_reading_level_skips_short_sections(monkeypatch) -> None:
    def fail_if_called(_text: str) -> float:
        raise AssertionError("short sections should be skipped")

    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        fail_if_called,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=6,
        section_payloads={
            "intro": IntroSection(
                title="Introduction",
                hook="Think about how authors choose details.",
                essential_question="Why does author purpose matter?",
                paragraphs=["Authors choose details clearly."],
                bridge_to_lesson="You will study those choices today.",
            )
        },
    )

    assert result.passed is True
    assert result.warnings == []


def test_validate_reading_level_uses_wider_band_for_lower_grades(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 5.0,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=4,
        section_payloads={
            "core_explainer": {
                "overview": (
                    "Fractions can be compared by naming equal parts and checking which "
                    "fraction covers more of the same whole before students explain the "
                    "result in class discussion."
                )
            }
        },
    )

    assert result.passed is True
    assert result.warnings == []


def test_validate_reading_level_still_warns_for_large_lower_grade_gap(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 6.5,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=4,
        section_payloads={
            "deep_dive": {
                "compare_focus": (
                    "Writers can shape reader interpretation through several layers of "
                    "purpose and evidence."
                ),
                "examples": [
                    {
                        "explanation": (
                            "An explanatory article often presents linked ideas, abstract "
                            "signals, and several details that ask readers to compare and "
                            "synthesize information before they can identify the author's "
                            "goal."
                        )
                    }
                ],
            }
        },
    )

    assert result.passed is True
    assert any("deep_dive" in warning for warning in result.warnings)
    assert any("above the target grade band" in warning for warning in result.warnings)


def test_validate_reading_level_uses_wider_band_for_grade_12_technical_content(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 13.0,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=12,
        section_payloads={
            "core_explainer": {
                "overview": (
                    "Hand hygiene interrupts pathogen transmission, reduces cross-contamination, "
                    "and protects patients during routine care when students follow each step "
                    "carefully and explain the safety reason in plain language."
                )
            }
        },
    )

    assert result.passed is True
    assert result.warnings == []


def test_validate_reading_level_allows_slightly_lower_grade_12_content(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 10.1,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=12,
        section_payloads={
            "core_explainer": {
                "overview": (
                    "Hand hygiene protects patients, interrupts pathogen spread, and gives future "
                    "healthcare workers a clear routine they can explain, practice, and apply in "
                    "clinical scenarios without using dense or overly technical wording."
                )
            }
        },
    )

    assert result.passed is True
    assert result.warnings == []


def test_validate_reading_level_still_warns_for_large_grade_12_gap(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 14.2,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=12,
        section_payloads={
            "core_explainer": {
                "overview": (
                    "Nosocomial transmission pathways, procedural noncompliance, and multilayered "
                    "clinical mitigation frameworks create compounding interpretation demands for "
                    "students who are still building fluency with technical healthcare discourse, "
                    "especially when the explanation layers abstract causal chains, operational "
                    "exceptions, and policy terminology into a single dense paragraph."
                )
            }
        },
    )

    assert result.passed is True
    assert any("core_explainer" in warning for warning in result.warnings)
    assert any("above the target grade band" in warning for warning in result.warnings)


def test_validate_reading_level_no_warn_for_grade_8_within_tolerance(
    monkeypatch,
) -> None:
    """Grade 8 target with score 9.2 is within the 1.25 tolerance; must not warn."""
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 9.2,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=8,
        section_payloads={
            "core_explainer": {
                "overview": (
                    "Democratic governments depend on citizens who understand how laws are "
                    "created, debated, and revised before they take effect in the legislature. "
                    "Students should be able to trace a bill through its stages and explain "
                    "the reasoning behind each procedural requirement before the final vote."
                )
            }
        },
    )

    assert result.passed is True
    assert result.warnings == []


def test_validate_reading_level_warns_for_grade_8_above_tolerance(
    monkeypatch,
) -> None:
    """Grade 8 target with score 10.5 exceeds the 2.0 tolerance; must warn."""
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 10.5,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=8,
        section_payloads={
            "core_explainer": {
                "overview": (
                    "Democratic governments depend on citizens who understand how laws are "
                    "created, debated, and revised before they take effect in the legislature. "
                    "Students should be able to trace a bill through its stages and explain "
                    "the reasoning behind each procedural requirement before the final vote."
                )
            }
        },
    )

    assert result.passed is True
    assert any("core_explainer" in warning for warning in result.warnings)
    assert any("above the target grade band" in warning for warning in result.warnings)


def test_validate_reading_level_warns_for_materially_lower_grade_12_gap(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        reading_level_module,
        "_flesch_kincaid_grade",
        lambda _text: 7.5,
    )

    result = reading_level_module.validate_reading_level(
        target_grade_level=12,
        section_payloads={
            "deep_dive": {
                "compare_focus": "Hand hygiene and infection control.",
                "examples": [
                    {
                        "explanation": (
                            "Wash your hands before care. Wash after care. Wash when you touch "
                            "shared tools. Wash again after contact with body fluids. Repeat each "
                            "step slowly and check the posted reminder so every action stays safe "
                            "for the patient and the healthcare worker on duty."
                        )
                    }
                ],
            }
        },
    )

    assert result.passed is True
    assert any("deep_dive" in warning for warning in result.warnings)
    assert any("below the target grade band" in warning for warning in result.warnings)
