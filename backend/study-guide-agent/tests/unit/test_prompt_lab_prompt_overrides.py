from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

import app.nodes.sections as sections_module
from app.nodes import blueprint as blueprint_module
from app.nodes.base import MAX_ANSWER_KEY_OUTPUT_TOKENS, MAX_OUTPUT_TOKENS
from app.nodes.sections import answer_key as answer_key_module
from app.nodes.sections import intro as intro_module
from app.types import Blueprint, GenerateRequest, PromptLabGenerateRequest


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
            },
            "sub_competencies": [
                item.model_dump() for item in request.curriculum.sub_competencies
            ],
            "core_concept": request.instructional_design.core_concept,
            "deep_dive_dimensions": ["entertain", "inform", "persuade"],
        }
    )


def _build_prompt_lab_request(
    base_request: GenerateRequest,
) -> PromptLabGenerateRequest:
    return PromptLabGenerateRequest.model_validate(
        {
            "base_request": base_request.model_dump(),
            "sample_case_id": "english_grade6_ph",
            "reviewer_label": "reviewer-a",
            "prompt_overrides": {
                "system_prompt_append": "Prefer crisp, classroom-ready wording.",
                "section_overrides": {
                    "intro": "Add one short sentence that previews the lesson task.",
                    "answer_key": "Keep teacher notes brief and practical.",
                },
            },
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


def _build_model_passage() -> dict[str, object]:
    return {
        "title": "Model Passage",
        "passage": [
            "The school talent show announcement uses an encouraging tone to encourage students to join.",
            "It highlights fun activities and invites readers to participate.",
        ],
    }


def _build_assessment_passage() -> dict[str, object]:
    return {
        "title": "Assessment Passage",
        "passage": [
            "Mangrove forests protect coastlines from strong waves.",
            "They help both people and wildlife stay safe.",
        ],
        "evidence_clues": ["protect coastlines", "stay safe"],
    }


def _build_assessment_questions() -> dict[str, object]:
    return {
        "title": "Assessment Questions",
        "questions": [
            {
                "number": 1,
                "question": "What is the author's purpose in this article?",
                "expected_response_type": "short_response",
                "evidence_hint": "Look for a phrase that explains why mangroves matter.",
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
async def test_prompt_lab_intro_override_appends_system_and_section_guidance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    prompt_lab_request = _build_prompt_lab_request(request)
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int = MAX_OUTPUT_TOKENS,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        assert "PH Grade 6 English" in system_prompt
        assert "Prefer crisp, classroom-ready wording." in system_prompt
        assert request.lesson_metadata.lesson_title in user_prompt
        assert "Add one short sentence that previews the lesson task." in user_prompt
        assert context_label == "intro"
        assert temperature == sections_module.TEMP_SECTION
        assert max_output_tokens == MAX_OUTPUT_TOKENS
        assert max_retries == 2

        return json.dumps(
            {
                "title": "Introduction",
                "hook": "A quick opening.",
                "essential_question": blueprint.essential_question,
                "paragraphs": ["Paragraph one.", "Paragraph two."],
                "bridge_to_lesson": "You will now apply these ideas.",
            }
        )

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await intro_module.generate_intro(prompt_lab_request, blueprint)

    assert result["title"] == "Introduction"


@pytest.mark.asyncio
async def test_prompt_lab_system_append_reaches_blueprint_without_section_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    prompt_lab_request = _build_prompt_lab_request(request)

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int = blueprint_module.MAX_BLUEPRINT_OUTPUT_TOKENS,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        assert "Prefer crisp, classroom-ready wording." in system_prompt
        assert "Competency code: EN6RC-Ia-2.2" in user_prompt
        assert (
            "Add one short sentence that previews the lesson task." not in user_prompt
        )
        assert context_label == "blueprint"
        assert temperature == blueprint_module.TEMP_BLUEPRINT
        assert max_output_tokens == blueprint_module.MAX_BLUEPRINT_OUTPUT_TOKENS
        assert max_retries == 2

        return json.dumps(
            {
                "lesson_id": request.lesson_metadata.lesson_code,
                "title": request.lesson_metadata.lesson_title,
                "essential_question": "Why does it matter why an author wrote something?",
                "introduction_hook": "Think about three messages with different purposes.",
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
                },
                "sub_competencies": [
                    item.model_dump() for item in request.curriculum.sub_competencies
                ],
                "core_concept": request.instructional_design.core_concept,
                "deep_dive_dimensions": ["entertain", "inform", "persuade"],
            }
        )

    monkeypatch.setattr(blueprint_module, "call_gemini", fake_call_gemini)

    result = await blueprint_module.generate_blueprint(prompt_lab_request)

    assert result.title == request.lesson_metadata.lesson_title


@pytest.mark.asyncio
async def test_prompt_lab_answer_key_override_applies_to_answer_key_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    prompt_lab_request = _build_prompt_lab_request(request)
    blueprint = _build_blueprint(request)
    check_in = _build_check_in()
    assessment_questions = _build_assessment_questions()
    step_up = _build_step_up()

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int = MAX_ANSWER_KEY_OUTPUT_TOKENS,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        check_in_questions = cast(list[dict[str, object]], check_in["questions"])
        assessment_question_list = cast(
            list[dict[str, object]], assessment_questions["questions"]
        )
        assert "Prefer crisp, classroom-ready wording." in system_prompt
        assert "Keep teacher notes brief and practical." in user_prompt
        assert str(check_in_questions[0]["question"]) in user_prompt
        assert str(assessment_question_list[0]["question"]) in user_prompt
        assert context_label == "answer_key"
        assert temperature == answer_key_module.TEMP_ANSWER_KEY
        assert max_output_tokens == MAX_ANSWER_KEY_OUTPUT_TOKENS
        assert max_retries == 2

        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [
                    {
                        "question_number": 1,
                        "question": str(check_in_questions[0]["question"]),
                        "possible_answer": "The announcement uses encouraging language to invite students to join.",
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
                    "challenge_response": "The article explains why mangroves matter and uses a direct quote as evidence.",
                    "required_evidence": ['"protect coastlines"'],
                },
                "teacher_note": "Accept brief answers with direct textual evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        prompt_lab_request,
        blueprint,
        _build_model_passage(),
        check_in,
        _build_assessment_passage(),
        assessment_questions,
        step_up,
    )

    assert (
        result["teacher_note"] == "Accept brief answers with direct textual evidence."
    )
