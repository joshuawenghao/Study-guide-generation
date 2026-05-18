from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from app.nodes.sections import answer_key as answer_key_module
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
                }
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


def _build_check_in() -> dict[str, object]:
    return {
        "title": "Check-In",
        "questions": [
            {
                "number": 1,
                "question": "What clues show the author's purpose?",
                "evidence_hint": "Look at the encouraging language.",
                "expected_response_type": "short_response",
            }
        ],
    }


def _build_assessment_passage() -> dict[str, object]:
    return {
        "title": "Assessment Passage",
        "passage": [
            "Mangrove forests protect coastlines from strong waves.",
            "They help both people and wildlife stay safe.",
        ],
    }


def _build_assessment_questions() -> dict[str, object]:
    return {
        "title": "Assessment Questions",
        "questions": [
            {
                "number": 1,
                "question": "What is the author's purpose in this article?",
                "question_type": "short_response",
                "answer_expectation": "Identify the purpose and explain it.",
                "evidence_requirement": "Quote a phrase that explains why mangroves matter.",
            }
        ],
    }


def _build_step_up() -> dict[str, object]:
    return {
        "title": "Step Up",
        "challenge_prompt": "Use evidence from the passage to explain the author's purpose.",
        "required_evidence": ['"protect coastlines"'],
        "success_criteria": [
            "Answers explain the purpose clearly.",
            "Answers use evidence from the passage.",
        ],
    }


@pytest.mark.asyncio
async def test_generate_answer_key_returns_structured_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    check_in = _build_check_in()
    assessment_passage = _build_assessment_passage()
    assessment_questions = _build_assessment_questions()
    step_up = _build_step_up()

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        check_in_questions = cast(list[dict[str, object]], check_in["questions"])
        assessment_question_list = cast(
            list[dict[str, object]], assessment_questions["questions"]
        )
        assert "PH Grade 6 English" in system_prompt
        assert str(check_in_questions[0]["question"]) in user_prompt
        assert str(assessment_question_list[0]["question"]) in user_prompt
        assert str(step_up["challenge_prompt"]) in user_prompt
        assert (
            '"Mangrove forests protect coastlines from strong waves."'
            not in user_prompt
        )
        assert "Mangrove forests protect coastlines from strong waves." in user_prompt
        assert temperature == answer_key_module.TEMP_ANSWER_KEY
        assert max_retries == 2
        assert context_label == "answer_key"

        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [
                    {
                        "question_number": 1,
                        "question": str(check_in_questions[0]["question"]),
                        "possible_answer": "The author uses an encouraging tone and says students should join the event because it will be fun.",
                        "evidence_quote": '"encouraging tone"',
                    }
                ],
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": str(assessment_question_list[0]["question"]),
                        "possible_answer": 'The author wants to inform and persuade readers because "protect coastlines" shows why mangroves matter.',
                        "evidence_quote": '"protect coastlines"',
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The author wants readers to care and act because the passage explains how mangroves protect communities.",
                    "required_evidence": ['"protect coastlines"'],
                },
                "teacher_note": "Accept answers that identify the purpose and cite a direct phrase from the passage.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        check_in,
        assessment_passage,
        assessment_questions,
        step_up,
    )

    assert result["title"] == "Answer Key"
    assert result["check_in_answers"][0]["question_number"] == 1
    assert result["assessment_answers"][0]["evidence_quote"] == '"protect coastlines"'
    assert result["step_up_answer"]["required_evidence"] == ['"protect coastlines"']


@pytest.mark.asyncio
async def test_generate_answer_key_raises_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return "not-json"

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    with pytest.raises(
        RuntimeError, match="Failed to parse answer_key response as JSON"
    ):
        await answer_key_module.generate_answer_key(
            request,
            blueprint,
            _build_check_in(),
            _build_assessment_passage(),
            _build_assessment_questions(),
            _build_step_up(),
        )
