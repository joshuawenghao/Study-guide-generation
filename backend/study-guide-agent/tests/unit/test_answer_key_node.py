from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from app.nodes.base import MAX_ANSWER_KEY_OUTPUT_TOKENS
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
            },
            "sub_competencies": [
                item.model_dump() for item in request.curriculum.sub_competencies
            ],
            "core_concept": request.instructional_design.core_concept,
            "deep_dive_dimensions": ["entertain", "inform", "persuade"],
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
        max_output_tokens: int = MAX_ANSWER_KEY_OUTPUT_TOKENS,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        check_in_questions = cast(list[dict[str, object]], check_in["questions"])
        assessment_question_list = cast(
            list[dict[str, object]], assessment_questions["questions"]
        )
        assert "PH Grade 6 English" in system_prompt
        assert str(check_in_questions[0]["question"]) in user_prompt
        assert "Model passage text for check-in answers:" in user_prompt
        assert "school talent show announcement uses an encouraging tone" in user_prompt
        assert "Exact quote bank for check-in answers" in user_prompt
        assert (
            '"The school talent show announcement uses an encouraging tone to encourage students to join."'
            in user_prompt
        )
        assert str(assessment_question_list[0]["question"]) in user_prompt
        assert "assessment_answers" in user_prompt
        assert str(step_up["challenge_prompt"]) in user_prompt
        assert '"Mangrove forests protect coastlines from strong waves."' in user_prompt
        assert "Mangrove forests protect coastlines from strong waves." in user_prompt
        assert '"protect coastlines"' in user_prompt
        assert (
            "Do not reuse a generic check-in evidence_quote for multiple different questions"
            in user_prompt
        )
        assert (
            "Provide one assessment_answers entry per assessment question"
            in user_prompt
        )
        assert temperature == answer_key_module.TEMP_ANSWER_KEY
        assert max_output_tokens == MAX_ANSWER_KEY_OUTPUT_TOKENS
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
                        "possible_answer": "The author wants to inform and persuade readers about why mangroves matter.",
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
        _build_model_passage(),
        check_in,
        assessment_passage,
        assessment_questions,
        step_up,
    )

    assert result["title"] == "Answer Key"
    assert result["check_in_answers"][0]["question_number"] == 1
    assert (
        result["assessment_answers"][0]["possible_answer"]
        == "The author wants to inform and persuade readers about why mangroves matter."
    )
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
            _build_model_passage(),
            _build_check_in(),
            _build_assessment_passage(),
            _build_assessment_questions(),
            _build_step_up(),
        )


@pytest.mark.asyncio
async def test_generate_answer_key_retries_truncated_json_with_higher_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    check_in = _build_check_in()
    assessment_passage = _build_assessment_passage()
    assessment_questions = _build_assessment_questions()
    step_up = _build_step_up()
    seen_budgets: list[int] = []

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int = MAX_ANSWER_KEY_OUTPUT_TOKENS,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        del system_prompt, user_prompt, temperature, max_retries, context_label
        seen_budgets.append(max_output_tokens)
        if len(seen_budgets) == 1:
            return (
                '{"title":"Answer Key","check_in_answers":[{'
                '"question_number":1,"question":"What clues show the author'
            )

        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [
                    {
                        "question_number": 1,
                        "question": str(
                            cast(list[dict[str, object]], check_in["questions"])[0][
                                "question"
                            ]
                        ),
                        "possible_answer": "The author uses an encouraging tone.",
                        "evidence_quote": '"encouraging tone"',
                    }
                ],
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": str(
                            cast(
                                list[dict[str, object]],
                                assessment_questions["questions"],
                            )[0]["question"]
                        ),
                        "possible_answer": "The author wants to inform readers about why mangroves matter.",
                        "evidence_quote": '"protect coastlines"',
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The passage explains how mangroves protect communities.",
                    "required_evidence": ['"protect coastlines"'],
                },
                "teacher_note": "Accept direct quotes from the passage.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        check_in,
        assessment_passage,
        assessment_questions,
        step_up,
    )

    assert result["title"] == "Answer Key"
    assert seen_budgets == [MAX_ANSWER_KEY_OUTPUT_TOKENS, 16384]


@pytest.mark.asyncio
async def test_generate_answer_key_repairs_missing_assessment_quote_from_evidence_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [],
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": "What is the author's purpose in this article?",
                        "possible_answer": "The author wants to inform readers about why mangroves matter.",
                        "evidence_quote": '"protect coastlines"',
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The author explains why mangroves protect communities.",
                    "required_evidence": ['"protect coastlines"'],
                },
                "teacher_note": "Accept answers that identify purpose and cite direct evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert (
        result["assessment_answers"][0]["possible_answer"]
        == "The author wants to inform readers about why mangroves matter."
    )
    assert result["assessment_answers"][0]["evidence_quote"] == '"protect coastlines"'


@pytest.mark.asyncio
async def test_generate_answer_key_repairs_nonverbatim_quote_to_exact_passage_phrase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [],
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": "What is the author's purpose in this article?",
                        "possible_answer": 'The author wants to inform readers because "protects coastlines" shows why mangroves matter.',
                        "evidence_quote": '"protects coastlines"',
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The author explains why mangroves protect communities.",
                    "required_evidence": ['"protect coastlines"'],
                },
                "teacher_note": "Accept answers that identify purpose and cite direct evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert result["assessment_answers"][0]["evidence_quote"] == '"protect coastlines"'
    assert (
        '"protect coastlines"' not in result["assessment_answers"][0]["possible_answer"]
    )
    assert (
        result["assessment_answers"][0]["question"]
        == "What is the author's purpose in this article?"
    )


@pytest.mark.asyncio
async def test_generate_answer_key_realigns_assessment_answers_to_upstream_questions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [],
                "assessment_answers": [
                    {
                        "question_number": 99,
                        "question": "What components were included in the program?",
                        "possible_answer": "The program improved infection control.",
                        "evidence_quote": '"protect coastlines"',
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The author explains why mangroves protect communities.",
                    "required_evidence": ['"protect coastlines"'],
                },
                "teacher_note": "Accept answers that identify purpose and cite direct evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert result["assessment_answers"] == [
        {
            "question_number": 1,
            "question": "What is the author's purpose in this article?",
            "possible_answer": "The author wants to inform readers that mangrove forests protect coastlines from strong waves.",
            "evidence_quote": '"protect coastlines"',
        }
    ]


@pytest.mark.asyncio
async def test_generate_answer_key_prefers_assessment_question_text_over_wrong_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    assessment_questions = {
        "title": "Assessment Questions",
        "questions": [
            {
                "number": 1,
                "question": "What is the author's purpose in this article?",
                "expected_response_type": "short_response",
                "evidence_hint": "Look for a phrase that explains why mangroves matter.",
            },
            {
                "number": 2,
                "question": "How does the passage show that mangroves help communities?",
                "expected_response_type": "short_response",
                "evidence_hint": "Look for the detail about strong waves.",
            },
        ],
    }

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [],
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": "How does the passage show that mangroves help communities?",
                        "possible_answer": "The passage shows that mangroves protect coastlines from strong waves and help people stay safe.",
                        "evidence_quote": '"protect coastlines"',
                    },
                    {
                        "question_number": 2,
                        "question": "What is the author's purpose in this article?",
                        "possible_answer": "The author wants to inform readers about why mangroves matter to coastal communities.",
                        "evidence_quote": '"protect coastlines"',
                    },
                ],
                "step_up_answer": {
                    "challenge_response": "The passage explains why the evidence matters.",
                    "required_evidence": ["protect coastlines"],
                },
                "teacher_note": "Accept concise answers that explain the purpose and cite evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        _build_assessment_passage(),
        assessment_questions,
        _build_step_up(),
    )

    assert result["assessment_answers"] == [
        {
            "question_number": 1,
            "question": "What is the author's purpose in this article?",
            "possible_answer": "The author wants to inform readers about why mangroves matter to coastal communities.",
            "evidence_quote": '"protect coastlines"',
        },
        {
            "question_number": 2,
            "question": "How does the passage show that mangroves help communities?",
            "possible_answer": "The passage shows that mangroves protect coastlines from strong waves and help people stay safe.",
            "evidence_quote": '"protect coastlines"',
        },
    ]


@pytest.mark.asyncio
async def test_generate_answer_key_ignores_guidance_like_evidence_hint_when_building_assessment_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    assessment_questions = {
        "title": "Assessment Questions",
        "questions": [
            {
                "number": 1,
                "question": "What is the author's purpose in this article?",
                "expected_response_type": "short_response",
                "evidence_hint": "Look for the phrase about protecting coastlines.",
            }
        ],
    }

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [],
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": "Different question",
                        "possible_answer": "Fallback answer.",
                        "evidence_quote": '"protect coastlines"',
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The author explains why mangroves protect communities.",
                    "required_evidence": ['"protect coastlines"'],
                },
                "teacher_note": "Accept answers that identify purpose and cite direct evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        _build_assessment_passage(),
        assessment_questions,
        _build_step_up(),
    )

    assert (
        result["assessment_answers"][0]["possible_answer"]
        == "The author wants to inform readers that mangrove forests protect coastlines from strong waves."
    )
    assert (
        '"protect coastlines"' not in result["assessment_answers"][0]["possible_answer"]
    )


@pytest.mark.asyncio
async def test_generate_answer_key_derives_assessment_answers_when_model_omits_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [
                    {
                        "question_number": 1,
                        "question": "What clues show the author's purpose?",
                        "possible_answer": "The text uses strong descriptive details to guide the reader.",
                        "evidence_quote": "N/A",
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The passage explains why the evidence matters.",
                    "required_evidence": ["protect coastlines"],
                },
                "teacher_note": "Accept concise answers that explain the purpose and cite evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert result["assessment_answers"] == [
        {
            "question_number": 1,
            "question": "What is the author's purpose in this article?",
            "possible_answer": "The author wants to inform readers that mangrove forests protect coastlines from strong waves.",
            "evidence_quote": '"protect coastlines"',
        }
    ]


@pytest.mark.asyncio
async def test_generate_answer_key_normalizes_null_check_in_evidence_quote(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [
                    {
                        "question_number": 1,
                        "question": "What clues show the author's purpose?",
                        "possible_answer": "The descriptive details guide the reader toward the main idea.",
                        "evidence_quote": None,
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The passage explains why the evidence matters.",
                    "required_evidence": ["protect coastlines"],
                },
                "teacher_note": "Accept concise answers that explain the purpose and cite evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert result["check_in_answers"][0]["evidence_quote"] == "N/A"


@pytest.mark.asyncio
async def test_generate_answer_key_realigns_check_in_answers_to_upstream_questions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
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
                    "challenge_response": "The passage explains why the evidence matters.",
                    "required_evidence": ["protect coastlines"],
                },
                "teacher_note": "Accept concise answers that explain the purpose and cite evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert result["check_in_answers"] == [
        {
            "question_number": 1,
            "question": "What clues show the author's purpose?",
            "possible_answer": "The encouraging language shows the author's purpose clearly.",
            "evidence_quote": '"encouraging tone"',
        }
    ]


@pytest.mark.asyncio
async def test_generate_answer_key_prefers_check_in_question_text_over_wrong_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    check_in = {
        "title": "Check-In",
        "questions": [
            {
                "number": 1,
                "question": "What clues show the author's purpose?",
                "evidence_hint": "Look at the encouraging language.",
                "expected_response_type": "short_response",
            },
            {
                "number": 2,
                "question": "What details teach the reader important facts?",
                "evidence_hint": "Look for factual statements.",
                "expected_response_type": "short_response",
            },
        ],
    }

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [
                    {
                        "question_number": 1,
                        "question": "What details teach the reader important facts?",
                        "possible_answer": "The factual details help the reader learn key information.",
                        "evidence_quote": "N/A",
                    },
                    {
                        "question_number": 2,
                        "question": "What clues show the author's purpose?",
                        "possible_answer": "The encouraging language shows the author's purpose clearly.",
                        "evidence_quote": '"encouraging tone"',
                    },
                ],
                "assessment_answers": [],
                "step_up_answer": {
                    "challenge_response": "The passage explains why the evidence matters.",
                    "required_evidence": ["protect coastlines"],
                },
                "teacher_note": "Accept concise answers that explain the purpose and cite evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        check_in,
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert result["check_in_answers"] == [
        {
            "question_number": 1,
            "question": "What clues show the author's purpose?",
            "possible_answer": "The encouraging language shows the author's purpose clearly.",
            "evidence_quote": '"encouraging tone"',
        },
        {
            "question_number": 2,
            "question": "What details teach the reader important facts?",
            "possible_answer": "The factual details help the reader learn key information.",
            "evidence_quote": "N/A",
        },
    ]


@pytest.mark.asyncio
async def test_generate_answer_key_normalizes_nonverbatim_check_in_evidence_quote(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    model_passage = {
        "title": "Model Passage",
        "passage": [
            "Before entering Mr. Reyes's room, perform hand hygiene.",
            "After providing care, remove your PPE carefully and perform hand hygiene again.",
        ],
    }
    check_in = {
        "title": "Check-In",
        "questions": [
            {
                "number": 1,
                "question": "How does the author emphasize the importance of hand hygiene in preventing infection?",
                "evidence_hint": "Notice how often hand hygiene is mentioned in the sequence of actions.",
                "expected_response_type": "multiple_choice",
            }
        ],
    }

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [
                    {
                        "question_number": 1,
                        "question": "How does the author emphasize the importance of hand hygiene in preventing infection?",
                        "possible_answer": "By mentioning hand hygiene before entering the room and again after removing PPE.",
                        "evidence_quote": '"Before entering Mr. Reyes\'s room, perform hand hygiene. After providing care, remove your PPE carefully and perform hand hygiene again."',
                    }
                ],
                "assessment_answers": [],
                "step_up_answer": {
                    "challenge_response": "The passage explains why the evidence matters.",
                    "required_evidence": ["protect coastlines"],
                },
                "teacher_note": "Accept concise answers that explain the purpose and cite evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        model_passage,
        check_in,
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert result["check_in_answers"][0]["question_number"] == 1
    assert (
        result["check_in_answers"][0]["question"]
        == "How does the author emphasize the importance of hand hygiene in preventing infection?"
    )
    assert (
        result["check_in_answers"][0]["possible_answer"]
        == "By mentioning hand hygiene before entering the room and again after removing PPE."
    )
    assert result["check_in_answers"][0]["evidence_quote"] in {
        '"Before entering Mr. Reyes\'s room, perform hand hygiene."',
        '"After providing care, remove your PPE carefully and perform hand hygiene again."',
    }


@pytest.mark.asyncio
async def test_generate_answer_key_realigns_swapped_check_in_answers_by_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    model_passage = {
        "title": "Model Passage",
        "passage": [
            "Before entering Mr. Reyes's room, Nurse Maria performs hand hygiene and prepares the needed supplies.",
            "Inside the room, Nurse Maria wears gloves and eye protection to avoid contact with potentially infectious materials.",
            "After the assessment, Nurse Maria removes her gloves carefully and performs hand hygiene again to avoid self-contamination.",
        ],
    }
    check_in = {
        "title": "Check-In",
        "questions": [
            {
                "number": 1,
                "question": "What specific actions does Nurse Maria take before even entering Mr. Reyes's room, and why are these actions important?",
                "evidence_hint": "Look for the sentence describing what Maria does immediately before entering the room.",
                "expected_response_type": "text",
            },
            {
                "number": 2,
                "question": "Identify two pieces of personal protective equipment (PPE) Nurse Maria uses when assessing Mr. Reyes. According to the passage, what is the purpose of using PPE in this scenario?",
                "evidence_hint": "Focus on the paragraph describing Maria's interaction with Mr. Reyes inside the room.",
                "expected_response_type": "text",
            },
            {
                "number": 3,
                "question": "Explain how Nurse Maria prevents self-contamination after assessing Mr. Reyes's wound. Why is this step crucial in preventing the spread of infection?",
                "evidence_hint": "Find the sentences that discuss removing gloves and performing hand hygiene.",
                "expected_response_type": "text",
            },
        ],
    }

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [
                    {
                        "question_number": 1,
                        "question": "What specific actions does Nurse Maria take before even entering Mr. Reyes's room, and why are these actions important?",
                        "possible_answer": "She performs hand hygiene and prepares supplies before entering, which reduces the risk of bringing germs into the room.",
                        "evidence_quote": '"Before entering Mr. Reyes\'s room, Nurse Maria performs hand hygiene and prepares the needed supplies."',
                    },
                    {
                        "question_number": 2,
                        "question": "Why is infection prevention important?",
                        "possible_answer": "After the assessment, Nurse Maria removes her gloves carefully and performs hand hygiene again to avoid self-contamination.",
                        "evidence_quote": '"After the assessment, Nurse Maria removes her gloves carefully and performs hand hygiene again to avoid self-contamination."',
                    },
                    {
                        "question_number": 3,
                        "question": "What equipment helps prevent exposure?",
                        "possible_answer": "She wears gloves and eye protection to avoid contact with potentially infectious materials.",
                        "evidence_quote": '"Inside the room, Nurse Maria wears gloves and eye protection to avoid contact with potentially infectious materials."',
                    },
                ],
                "assessment_answers": [],
                "step_up_answer": {
                    "challenge_response": "The passage explains why the evidence matters.",
                    "required_evidence": ["protect coastlines"],
                },
                "teacher_note": "Accept concise answers that explain the purpose and cite evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        model_passage,
        check_in,
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert result["check_in_answers"] == [
        {
            "question_number": 1,
            "question": "What specific actions does Nurse Maria take before even entering Mr. Reyes's room, and why are these actions important?",
            "possible_answer": "She performs hand hygiene and prepares supplies before entering, which reduces the risk of bringing germs into the room.",
            "evidence_quote": '"Before entering Mr. Reyes\'s room, Nurse Maria performs hand hygiene and prepares the needed supplies."',
        },
        {
            "question_number": 2,
            "question": "Identify two pieces of personal protective equipment (PPE) Nurse Maria uses when assessing Mr. Reyes. According to the passage, what is the purpose of using PPE in this scenario?",
            "possible_answer": "She wears gloves and eye protection to avoid contact with potentially infectious materials.",
            "evidence_quote": '"Inside the room, Nurse Maria wears gloves and eye protection to avoid contact with potentially infectious materials."',
        },
        {
            "question_number": 3,
            "question": "Explain how Nurse Maria prevents self-contamination after assessing Mr. Reyes's wound. Why is this step crucial in preventing the spread of infection?",
            "possible_answer": "After the assessment, Nurse Maria removes her gloves carefully and performs hand hygiene again to avoid self-contamination.",
            "evidence_quote": '"After the assessment, Nurse Maria removes her gloves carefully and performs hand hygiene again to avoid self-contamination."',
        },
    ]


@pytest.mark.asyncio
async def test_generate_answer_key_ignores_model_paraphrase_when_selecting_assessment_quote(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [],
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": "What is the author's purpose in this article?",
                        "possible_answer": 'The author wants readers to care because "the mangrove roots keep every shoreline family safe during strong storms".',
                        "evidence_quote": '"the mangrove roots keep every shoreline family safe during strong storms"',
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The passage explains why the evidence matters.",
                    "required_evidence": ["protect coastlines"],
                },
                "teacher_note": "Accept concise answers that explain the purpose and cite evidence.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        _build_assessment_passage(),
        _build_assessment_questions(),
        _build_step_up(),
    )

    assert result["assessment_answers"][0]["evidence_quote"] == '"protect coastlines"'
    assert (
        '"protect coastlines"' not in result["assessment_answers"][0]["possible_answer"]
    )


@pytest.mark.asyncio
async def test_generate_answer_key_keeps_substantive_number_aligned_nursing_assessment_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    assessment_passage = {
        "title": "Assessment Passage",
        "passage": [
            "Before entering Mr. Reyes's room, Nurse Maria performs hand hygiene and prepares the needed supplies.",
            "Inside the room, Nurse Maria wears gloves and eye protection to avoid contact with potentially infectious materials.",
            "After the assessment, Nurse Maria removes her gloves carefully and performs hand hygiene again to avoid self-contamination.",
        ],
        "evidence_clues": [
            "performs hand hygiene and prepares the needed supplies",
            "wears gloves and eye protection",
            "performs hand hygiene again to avoid self-contamination",
        ],
    }
    assessment_questions = {
        "title": "Assessment Questions",
        "questions": [
            {
                "number": 1,
                "question": "What specific actions does Nurse Maria take before even entering Mr. Reyes's room, and why are these actions important?",
                "expected_response_type": "Short answer",
                "evidence_hint": "Look for the sentence describing what Maria does immediately before entering the room.",
            }
        ],
    }

    detailed_answer = "She cleans her hands and gets the supplies ready before entering so she can begin care without carrying germs into the room or delaying sterile work."

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Answer Key",
                "check_in_answers": [],
                "assessment_answers": [
                    {
                        "question_number": 1,
                        "question": "How does Nurse Maria prepare herself before patient contact?",
                        "possible_answer": detailed_answer,
                        "evidence_quote": '"Before entering Mr. Reyes\'s room, Nurse Maria performs hand hygiene and prepares the needed supplies."',
                    }
                ],
                "step_up_answer": {
                    "challenge_response": "The passage explains why the evidence matters.",
                    "required_evidence": [
                        "performs hand hygiene and prepares the needed supplies"
                    ],
                },
                "teacher_note": "Accept answers that explain how the nurse prevents infection before care begins.",
            }
        )

    monkeypatch.setattr(answer_key_module, "call_gemini", fake_call_gemini)

    result = await answer_key_module.generate_answer_key(
        request,
        blueprint,
        _build_model_passage(),
        _build_check_in(),
        assessment_passage,
        assessment_questions,
        _build_step_up(),
    )

    assert result["assessment_answers"] == [
        {
            "question_number": 1,
            "question": "What specific actions does Nurse Maria take before even entering Mr. Reyes's room, and why are these actions important?",
            "possible_answer": detailed_answer,
            "evidence_quote": '"Before entering Mr. Reyes\'s room, Nurse Maria performs hand hygiene and prepares the needed supplies."',
        }
    ]
