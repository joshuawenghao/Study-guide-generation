from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

import app.nodes.sections as sections_module
from app.nodes.sections import answer_key as answer_key_module
from app.nodes.sections import intro as intro_module
from app.nodes.sections import step_up as step_up_module
from app.nodes.sections import vocabulary as vocabulary_module
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
            ],
            "vocabulary": [
                {
                    "word": "author's purpose",
                    "definition": "The reason an author writes a text.",
                    "example_sentence": "We looked for the author's purpose before answering the questions.",
                },
                {
                    "word": "tone",
                    "definition": "The feeling or attitude shown in writing.",
                    "example_sentence": "The serious tone helped show that the text was meant to inform.",
                },
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
        "topic_domain": "mangrove forest protection article",
        "passage": [
            "Mangrove forests protect coastlines from strong waves and provide homes for many animals.",
            "The article urges communities to care for mangroves because they help both people and wildlife.",
        ],
        "evidence_clues": ["protect coastlines", "help both people and wildlife"],
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
                "evidence_requirement": "Quote a phrase that shows why mangroves matter.",
            }
        ],
    }


@pytest.mark.asyncio
async def test_representative_wave1_section_nodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

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

        return json.dumps(
            {
                "title": context_label.replace("_", " ").title(),
                "context_label": context_label,
                "items": [request.lesson_metadata.lesson_code],
            }
        )

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    checks = [
        (intro_module.generate_intro, "intro"),
        (vocabulary_module.generate_vocabulary, "vocabulary"),
    ]

    for generator, expected_label in checks:
        result = await generator(request, blueprint)
        assert result["context_label"] == expected_label
        assert result["items"] == [request.lesson_metadata.lesson_code]


@pytest.mark.asyncio
async def test_dependency_aware_wave3_step_up_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
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
        assessment_passage_lines = cast(list[str], assessment_passage["passage"])
        assessment_question_list = cast(
            list[dict[str, object]], assessment_questions["questions"]
        )

        assert "PH Grade 6 English" in system_prompt
        assert assessment_passage_lines[0] in user_prompt
        assert str(assessment_question_list[0]["question"]) in user_prompt
        assert temperature == sections_module.TEMP_SECTION
        assert max_retries == 2
        assert context_label == "step_up"

        return json.dumps(
            {
                "title": "Step Up",
                "context_label": context_label,
                "items": [request.lesson_metadata.lesson_code],
            }
        )

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await step_up_module.generate_step_up(
        request,
        blueprint,
        assessment_passage,
        assessment_questions,
    )

    assert result["context_label"] == "step_up"
    assert result["items"] == [request.lesson_metadata.lesson_code]


@pytest.mark.asyncio
async def test_answer_key_output_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    check_in = _build_check_in()
    assessment_passage = _build_assessment_passage()
    assessment_questions = _build_assessment_questions()
    step_up = {
        "title": "Step Up",
        "challenge_prompt": "Use evidence from the passage to explain the author's purpose.",
        "required_evidence": ['"protect coastlines"'],
        "success_criteria": ["Answers use passage evidence."],
    }

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
                        "possible_answer": "The author uses an encouraging tone.",
                        "evidence_quote": '"encouraging tone"',
                    }
                ],
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": str(assessment_question_list[0]["question"]),
                        "possible_answer": 'The author wants to inform readers because "protect coastlines" explains why mangroves matter.',
                        "evidence_quote": '"protect coastlines"',
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The author informs and persuades by showing how mangroves protect coastlines.",
                    "required_evidence": ['"protect coastlines"'],
                },
                "teacher_note": "Accept direct quotes from the passage.",
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

    assert result.keys() == {
        "title",
        "check_in_answers",
        "assessment_answers",
        "step_up_answer",
        "teacher_note",
    }
    assert result["check_in_answers"][0]["question_number"] == 1
    assert result["assessment_answers"][0]["evidence_quote"] == '"protect coastlines"'
