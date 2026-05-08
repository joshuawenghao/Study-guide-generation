from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.nodes.sections as sections_module
from app.nodes.sections import assessment_questions as assessment_questions_module
from app.nodes.sections import check_in as check_in_module
from app.nodes.sections import step_up as step_up_module
from app.types import Blueprint, GenerateRequest


def _load_request_from_fixture() -> GenerateRequest:
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "legacy_evals"
        / "english_grade6_ph.json"
    )
    fixture_payload = json.loads(fixture_path.read_text())
    fixture_input = fixture_payload["input"]
    fixture_input.setdefault("optional", {})
    return GenerateRequest.model_validate(fixture_input)


def _build_blueprint(request: GenerateRequest) -> Blueprint:
    return Blueprint.model_validate(
        {
            "lesson_id": request.lesson_metadata.lesson_code,
            "title": request.lesson_metadata.lesson_title,
            "essential_question": "Why does it matter why an author wrote something?",
            "introduction_hook": "Compare three texts about the same topic that each try to do something different.",
            "learning_targets": [
                {
                    "number": 1,
                    "bloom_verb": request.instructional_design.bloom_targets[0],
                    "objective": "I can identify the three main author purposes: entertain, inform, and persuade.",
                },
                {
                    "number": 2,
                    "bloom_verb": request.instructional_design.bloom_targets[1],
                    "objective": "I can explain how language and tone show an author's purpose.",
                },
                {
                    "number": 3,
                    "bloom_verb": request.instructional_design.bloom_targets[2],
                    "objective": "I can apply purpose identification to a new passage.",
                },
            ],
            "vocabulary": [
                {
                    "word": "author's purpose",
                    "definition": "The reason an author writes a text.",
                    "example_sentence": "We looked for the author's purpose before answering the questions.",
                }
            ],
            "topic_domains": {
                "model_passage": "school talent show announcement",
                "assessment_passage": "mangrove forest protection article",
                "entertain_example": "barangay festival story",
                "inform_example": "typhoon safety guide",
                "persuade_example": "clean classroom campaign",
            },
            "sub_competencies": [
                item.model_dump() for item in request.curriculum.sub_competencies
            ],
            "core_concept": request.instructional_design.core_concept,
        }
    )


def _build_model_passage() -> dict[str, object]:
    return {
        "title": "Model Passage",
        "topic_domain": "school talent show announcement",
        "genre": "announcement",
        "passage": [
            "The student council posted a cheerful announcement about the upcoming talent show.",
            "It encouraged students to join and described how the event would entertain the school community.",
        ],
        "text_features": ["enthusiastic tone", "event details"],
        "evidence_focus": "Look for clues that show the writer wants readers to look forward to the event.",
    }


def _build_assessment_passage() -> dict[str, object]:
    return {
        "title": "Assessment Passage",
        "topic_domain": "mangrove forest protection article",
        "genre": "article",
        "passage": [
            "Mangrove forests protect coastlines from strong waves and provide homes for many animals.",
            "The article urges communities to care for mangroves because they help both people and wildlife.",
        ],
        "evidence_clues": ["protect coastlines", "help both people and wildlife"],
        "answerability_note": "Questions should be answerable from the stated reasons and examples in the article.",
    }


def _build_assessment_questions() -> dict[str, object]:
    return {
        "title": "Assessment Questions",
        "passage_title": "Assessment Passage",
        "questions": [
            {
                "number": 1,
                "question": "What is the author's purpose in this article?",
                "question_type": "short_response",
                "answer_expectation": "Identify the purpose and explain it.",
                "evidence_requirement": "Quote a phrase that shows why mangroves matter.",
            }
        ],
    }


@pytest.mark.asyncio
async def test_wave3_section_nodes_generate_structured_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    model_passage = _build_model_passage()
    assessment_passage = _build_assessment_passage()
    assessment_questions = _build_assessment_questions()

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        assert "PH Grade 6 English" in system_prompt
        assert request.lesson_metadata.lesson_title in user_prompt
        assert temperature == sections_module.TEMP_SECTION
        assert max_retries == 2

        expected_fragments: dict[str, list[str]] = {
            "check_in": [
                str(model_passage["passage"][0]),
                str(model_passage["evidence_focus"]),
            ],
            "assessment_questions": [
                str(assessment_passage["passage"][0]),
                str(assessment_passage["evidence_clues"][0]),
            ],
            "step_up": [
                str(assessment_passage["passage"][0]),
                str(assessment_questions["questions"][0]["question"]),
            ],
        }
        for fragment in expected_fragments[context_label]:
            assert fragment in user_prompt

        return json.dumps(
            {
                "title": context_label.replace("_", " ").title(),
                "context_label": context_label,
                "items": [request.lesson_metadata.lesson_code],
            }
        )

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    checks = [
        (
            check_in_module.generate_check_in,
            "check_in",
            [model_passage],
        ),
        (
            assessment_questions_module.generate_assessment_questions,
            "assessment_questions",
            [assessment_passage],
        ),
        (
            step_up_module.generate_step_up,
            "step_up",
            [assessment_passage, assessment_questions],
        ),
    ]

    for generator, expected_label, extra_args in checks:
        result = await generator(request, blueprint, *extra_args)

        assert result["context_label"] == expected_label
        assert result["items"] == [request.lesson_metadata.lesson_code]


@pytest.mark.asyncio
async def test_wave3_section_nodes_raise_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    model_passage = _build_model_passage()

    async def fake_call_gemini(**_: object) -> str:
        return "not-json"

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    with pytest.raises(RuntimeError, match="Failed to parse check_in response as JSON"):
        await check_in_module.generate_check_in(request, blueprint, model_passage)
