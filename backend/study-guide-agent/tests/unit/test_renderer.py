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
        "check_in": {
            "title": "Check-In",
            "passage_title": "Model Passage",
            "questions": [
                {
                    "number": 1,
                    "question": "What clues show the author's purpose?",
                    "evidence_hint": "Look at the encouraging language.",
                    "expected_response_type": "short_response",
                }
            ],
        },
        "assessment_passage": {
            "title": "Assessment Passage",
            "topic_domain": "mangrove forest protection article",
            "genre": "informational article",
            "passage": [
                "Mangrove forests protect coastlines from strong waves.",
                "They help both people and wildlife stay safe.",
            ],
            "evidence_clues": ["protect coastlines", "stay safe"],
            "answerability_note": "Each question can be answered using direct evidence from the passage.",
        },
        "assessment_questions": {
            "title": "Assessment Questions",
            "passage_title": "Assessment Passage",
            "questions": [
                {
                    "number": 1,
                    "question": "What is the author's purpose in this article?",
                    "question_type": "short_response",
                    "answer_expectation": "Identify the purpose and explain it.",
                    "evidence_requirement": "Quote a phrase that explains why mangroves matter.",
                }
            ],
        },
        "answer_key": {
            "title": "Answer Key",
            "check_in_answers": [
                {
                    "question_number": 99,
                    "question": "What details were most convincing?",
                    "possible_answer": "The encouraging language shows the author's purpose clearly.",
                    "evidence_quote": '"encouraging tone"',
                }
            ],
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


def build_sections_missing_evidence_quote() -> dict[str, object]:
    sections = build_sections()
    sections["answer_key"] = {
        "title": "Answer Key",
        "check_in_answers": [
            {
                "question_number": 1,
                "question": "What is the clue?",
                "possible_answer": "The command shows persuasion.",
            }
        ],
        "assessment_answers": [
            {
                "question_number": 2,
                "question": "Why does the passage inform?",
                "possible_answer": 'It informs because "protect coastlines" explains the idea.',
            }
        ],
        "step_up_answer": {
            "challenge_response": "Use passage evidence to explain the purpose.",
            "required_evidence": ["quoted phrase"],
        },
        "teacher_note": "Accept equivalent answers with evidence.",
    }
    return sections


def build_sections_string_step_up_answer() -> dict[str, object]:
    sections = build_sections()
    sections["answer_key"] = {
        "title": "Answer Key",
        "check_in_answers": [],
        "assessment_answers": [],
        "step_up_answer": "Use passage evidence to explain the purpose.",
        "teacher_note": "Accept equivalent answers with evidence.",
    }
    return sections


@pytest.mark.asyncio
async def test_generate_rendered_response_returns_pdf_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_html: dict[str, str] = {}

    def fake_render_pdf_bytes(html: str) -> bytes:
        captured_html["value"] = html
        assert '<svg class="icon-svg"' in html
        assert 'class="heading-icon"' in html
        assert 'class="callout-icon"' in html
        return b"%PDF-1.7\nrenderer-test\n"

    monkeypatch.setattr(
        renderer_module,
        "_render_pdf_bytes",
        fake_render_pdf_bytes,
    )

    response = await renderer_module.generate_rendered_response(
        blueprint=build_blueprint(),
        sections=build_sections(),
        validation=build_validation(),
    )

    pdf_bytes = base64.b64decode(response.pdf_base64)

    assert response.success is True
    assert pdf_bytes.startswith(b"%PDF")
    assert "value" in captured_html
    assert "Validation Notes" not in captured_html["value"]
    assert (
        "Reading level slightly above target for intro." not in captured_html["value"]
    )
    assert "What clues show the author" in captured_html["value"]
    assert "What details were most convincing?" not in captured_html["value"]


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
        "check_in",
        "assessment_passage",
        "assessment_questions",
        "answer_key",
    ]
    assert [section.icon_key for section in response.preview.sections] == [
        "spark",
        "layers",
        "layers",
        "message-check",
        "clipboard-notes",
        "pencil",
        "key",
    ]


@pytest.mark.asyncio
async def test_generate_rendered_response_tolerates_missing_answer_key_evidence_quote(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        renderer_module,
        "_render_pdf_bytes",
        lambda _html: b"%PDF-1.7\nrenderer-test\n",
    )

    response = await renderer_module.generate_rendered_response(
        blueprint=build_blueprint(),
        sections=build_sections_missing_evidence_quote(),
        validation=build_validation(),
    )

    pdf_bytes = base64.b64decode(response.pdf_base64)

    assert response.success is True
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_generate_rendered_response_tolerates_string_step_up_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        renderer_module,
        "_render_pdf_bytes",
        lambda _html: b"%PDF-1.7\nrenderer-test\n",
    )

    response = await renderer_module.generate_rendered_response(
        blueprint=build_blueprint(),
        sections=build_sections_string_step_up_answer(),
        validation=build_validation(),
    )

    pdf_bytes = base64.b64decode(response.pdf_base64)

    assert response.success is True
    assert pdf_bytes.startswith(b"%PDF")
