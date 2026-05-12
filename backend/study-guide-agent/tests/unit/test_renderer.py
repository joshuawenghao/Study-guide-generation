from __future__ import annotations

import base64

import pytest

from app.nodes import renderer as renderer_module
from app.types import (
    Blueprint,
    LearningTarget,
    SubCompetency,
    TopicDomains,
    ValidationResult,
    VocabEntry,
)


def build_blueprint() -> Blueprint:
    return Blueprint(
        lesson_id="ENG6-U1-L2",
        title="Author's Purpose",
        essential_question="Why does author purpose matter?",
        introduction_hook="Texts can guide readers in different ways.",
        learning_targets=[
            LearningTarget(
                number=1,
                bloom_verb="identify",
                objective="Identify how authors signal purpose.",
            )
        ],
        vocabulary=[
            VocabEntry(
                word="audience",
                definition="The people a text is meant for.",
                example_sentence="The writer considered the audience before choosing details.",
            )
        ],
        topic_domains=TopicDomains(
            model_passage="school talent show announcement",
            assessment_passage="mangrove forest protection article",
            entertain_example="games",
            inform_example="science",
            persuade_example="community",
        ),
        sub_competencies=[SubCompetency(id="sc-1", label="Purpose clues")],
        core_concept="Authors choose details for a purpose.",
    )


def build_validation() -> ValidationResult:
    return ValidationResult(
        passed=True,
        failed_sections=[],
        failures={},
        warnings=["Reading level slightly above target for intro."],
        best_effort_sections=[],
    )


def build_sections() -> dict[str, object]:
    return {
        "answer_key": {
            "title": "Answer Key",
            "check_in_answers": [],
            "assessment_answers": [],
            "step_up_answer": {
                "challenge_response": "Use passage evidence to explain the purpose.",
                "required_evidence": ["quoted phrase"],
            },
            "teacher_note": "Accept equivalent answers with evidence.",
        },
        "subconcept": [
            {
                "title": "Subconcept One",
                "sub_competency_id": "sc-1",
                "sub_competency_label": "Purpose clues",
                "explanation": "Clues in a text reveal purpose.",
                "worked_example": "A poster uses commands to persuade.",
                "quick_check": {
                    "question": "What clue shows persuasion?",
                    "expected_answer": "The command tells the reader what to do.",
                },
            },
            {
                "title": "Subconcept Two",
                "sub_competency_id": "sc-1",
                "sub_competency_label": "Purpose clues",
                "explanation": "Tone supports the writer's goal.",
                "worked_example": "An article uses factual language to inform.",
                "quick_check": {
                    "question": "What clue shows informing?",
                    "expected_answer": "The factual language teaches the reader.",
                },
            },
        ],
        "intro": {
            "title": "Introduction",
            "hook": "Think about how authors choose details.",
            "essential_question": "Why does author purpose matter?",
            "paragraphs": ["Authors choose details to guide the reader clearly."],
            "bridge_to_lesson": "You will study those choices today.",
        },
    }


@pytest.mark.asyncio
async def test_generate_rendered_response_returns_pdf_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        renderer_module,
        "_render_pdf_bytes",
        lambda _html: b"%PDF-1.7\nrenderer-test\n",
    )

    response = await renderer_module.generate_rendered_response(
        blueprint=build_blueprint(),
        sections=build_sections(),
        validation=build_validation(),
    )

    pdf_bytes = base64.b64decode(response.pdf_base64)

    assert response.success is True
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_generate_rendered_response_orders_preview_sections_canonically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        renderer_module,
        "_render_pdf_bytes",
        lambda _html: b"%PDF-1.7\nrenderer-test\n",
    )

    response = await renderer_module.generate_rendered_response(
        blueprint=build_blueprint(),
        sections=build_sections(),
        validation=build_validation(),
    )

    assert [section.section_id for section in response.preview.sections] == [
        "intro",
        "subconcept-1",
        "subconcept-2",
        "answer_key",
    ]
