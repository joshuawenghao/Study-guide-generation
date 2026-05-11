from __future__ import annotations

from app.validators.hard.json_schema import validate_json_schema


def test_validate_json_schema_passes_for_valid_intro_payload() -> None:
    result = validate_json_schema(
        section_key="intro",
        payload={
            "title": "Introduction",
            "hook": "Look at how three texts can guide readers in different ways.",
            "essential_question": "Why does it matter why an author wrote something?",
            "paragraphs": [
                "Authors make choices based on what they want readers to think, feel, or do.",
                "Studying those choices helps you explain a text with evidence.",
            ],
            "bridge_to_lesson": "This opening leads into the study guide sections that help you identify author purpose.",
        },
    )

    assert result.passed is True
    assert result.failed_sections == []
    assert result.failures == {}


def test_validate_json_schema_reports_field_failures() -> None:
    result = validate_json_schema(
        section_key="intro",
        payload={
            "title": "Introduction",
            "hook": "A hook",
            "essential_question": "An essential question",
            "paragraphs": "not-a-list",
        },
    )

    assert result.passed is False
    assert result.failed_sections == ["intro"]
    assert "intro" in result.failures
    assert any("paragraphs" in message for message in result.failures["intro"])
    assert any("bridge_to_lesson" in message for message in result.failures["intro"])
