from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.nodes.sections as sections_module
from app.nodes.base import MAX_OUTPUT_TOKENS
from app.nodes.sections import (
    intro as intro_module,
)
from app.nodes.sections import (
    key_points as key_points_module,
)
from app.nodes.sections import (
    learning_targets as learning_targets_module,
)
from app.nodes.sections import (
    self_assessment as self_assessment_module,
)
from app.nodes.sections import (
    vocabulary as vocabulary_module,
)
from app.nodes.sections import (
    warmup as warmup_module,
)
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
                },
                {
                    "word": "entertain",
                    "definition": "To make the reader enjoy the text.",
                    "example_sentence": "The funny story was written to entertain the reader.",
                },
                {
                    "word": "inform",
                    "definition": "To teach or give facts to the reader.",
                    "example_sentence": "The article was written to inform us about volcano safety.",
                },
                {
                    "word": "persuade",
                    "definition": "To convince the reader to think or do something.",
                    "example_sentence": "The poster tried to persuade students to recycle.",
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
            },
            "sub_competencies": [
                item.model_dump() for item in request.curriculum.sub_competencies
            ],
            "core_concept": request.instructional_design.core_concept,
            "deep_dive_dimensions": ["entertain", "inform", "persuade"],
        }
    )


@pytest.mark.asyncio
async def test_wave1_section_nodes_generate_structured_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
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
        assert request.lesson_metadata.lesson_title in user_prompt
        assert temperature == sections_module.TEMP_SECTION
        assert max_output_tokens == MAX_OUTPUT_TOKENS
        assert max_retries == 2

        return json.dumps(
            {
                "title": context_label.replace("_", " ").title(),
                "context_label": context_label,
                "items": [request.lesson_metadata.lesson_code],
            }
        )

    modules = [
        (intro_module, intro_module.generate_intro, "intro"),
        (
            learning_targets_module,
            learning_targets_module.generate_learning_targets,
            "learning_targets",
        ),
        (warmup_module, warmup_module.generate_warmup, "warmup"),
        (vocabulary_module, vocabulary_module.generate_vocabulary, "vocabulary"),
        (key_points_module, key_points_module.generate_key_points, "key_points"),
        (
            self_assessment_module,
            self_assessment_module.generate_self_assessment,
            "self_assessment",
        ),
    ]

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    for _, generator, expected_label in modules:
        result = await generator(request, blueprint)

        assert result["context_label"] == expected_label
        assert result["items"] == [request.lesson_metadata.lesson_code]


@pytest.mark.asyncio
async def test_wave1_section_nodes_raise_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return "not-json"

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    with pytest.raises(RuntimeError, match="Failed to parse intro response as JSON"):
        await intro_module.generate_intro(request, blueprint)


@pytest.mark.asyncio
async def test_wave1_section_nodes_repair_mismatched_json_closers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return (
            '{ "title": "Key Points", "points": [ '
            '{ "number": 1, '
            '"sub_competency_id": "SC-1", '
            '"sub_competency_label": '
            '"Identify and apply hand hygiene, PPE, and aseptic handling steps in routine nursing tasks.", '
            '"statement": '
            '"Consistently perform hand hygiene, use appropriate personal protective equipment (PPE) like gloves and masks, and follow aseptic techniques to prevent infection during all nursing tasks." '
            "] }"
        )

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await key_points_module.generate_key_points(request, blueprint)

    assert result == {
        "title": "Key Points",
        "points": [
            {
                "number": 1,
                "sub_competency_id": "SC-1",
                "sub_competency_label": "Identify and apply hand hygiene, PPE, and aseptic handling steps in routine nursing tasks.",
                "statement": "Consistently perform hand hygiene, use appropriate personal protective equipment (PPE) like gloves and masks, and follow aseptic techniques to prevent infection during all nursing tasks.",
            }
        ],
    }


@pytest.mark.asyncio
async def test_wave1_section_nodes_retry_truncated_json_with_higher_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    seen_budgets: list[int] = []

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int = sections_module.MAX_OUTPUT_TOKENS,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        del system_prompt, user_prompt, temperature, max_retries, context_label
        seen_budgets.append(max_output_tokens)
        if len(seen_budgets) == 1:
            return (
                '{"title":"Introduction","hook":"A quick opening.",'
                '"essential_question":"Why does it matter why an author wrote something?",'
                '"paragraphs":["Paragraph one.","Paragraph two."],'
                '"bridge_to_lesson":"You will now'
            )

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

    result = await intro_module.generate_intro(request, blueprint)

    assert result["title"] == "Introduction"
    assert seen_budgets == [sections_module.MAX_OUTPUT_TOKENS, 4096]
