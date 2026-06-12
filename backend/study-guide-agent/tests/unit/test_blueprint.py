from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.nodes import blueprint as blueprint_module
from app.types import GenerateRequest


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


@pytest.mark.asyncio
async def test_generate_blueprint_returns_valid_blueprint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int = blueprint_module.MAX_BLUEPRINT_OUTPUT_TOKENS,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        assert "PH Grade 6 English" in system_prompt
        assert "Competency code: EN6RC-Ia-2.2" in user_prompt
        assert temperature == blueprint_module.TEMP_BLUEPRINT
        assert max_output_tokens == blueprint_module.MAX_BLUEPRINT_OUTPUT_TOKENS
        assert max_retries == 2
        assert context_label == "blueprint"

        return json.dumps(
            {
                "lesson_id": request.lesson_metadata.lesson_code,
                "title": request.lesson_metadata.lesson_title,
                "essential_question": "Why does it matter why an author wrote something?",
                "introduction_hook": "Think about three messages that all talk about the same topic but try to do different things.",
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
                    "assessment_passage": "mangrove forest protection article",                },
                "sub_competencies": [
                    item.model_dump() for item in request.curriculum.sub_competencies
                ],
                "core_concept": request.instructional_design.core_concept,
                "deep_dive_dimensions": ["entertain", "inform", "persuade"],
            }
        )

    monkeypatch.setattr(blueprint_module, "call_gemini", fake_call_gemini)

    result = await blueprint_module.generate_blueprint(request)

    assert set(result.model_dump().keys()) == {
        "lesson_id",
        "title",
        "essential_question",
        "introduction_hook",
        "learning_targets",
        "vocabulary",
        "topic_domains",
        "sub_competencies",
        "core_concept",
        "deep_dive_dimensions",
    }
    assert result.lesson_id == "E6_Q1_0201"
    assert result.title == "Identifying Author's Purpose"
    assert result.essential_question
    assert result.introduction_hook
    assert result.core_concept == request.instructional_design.core_concept
    assert len(result.learning_targets) == 3
    assert len(result.sub_competencies) == 3
    assert len(result.vocabulary) == 5
    assert result.topic_domains.model_passage != result.topic_domains.assessment_passage


@pytest.mark.asyncio
async def test_generate_blueprint_retries_truncated_json_with_higher_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    seen_budgets: list[int] = []

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int = blueprint_module.MAX_BLUEPRINT_OUTPUT_TOKENS,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        del system_prompt, user_prompt, temperature, max_retries, context_label
        seen_budgets.append(max_output_tokens)
        if len(seen_budgets) == 1:
            return '{"lesson_id":"HN12-U3-L2","title":"Standard Precautions"'

        return json.dumps(
            {
                "lesson_id": request.lesson_metadata.lesson_code,
                "title": request.lesson_metadata.lesson_title,
                "essential_question": "How do nurses use standard precautions to protect themselves and their patients?",
                "introduction_hook": "Think about how one missed precaution can affect an entire ward.",
                "learning_targets": [
                    {
                        "number": 1,
                        "bloom_verb": request.instructional_design.bloom_targets[0],
                        "objective": "I can identify situations that require standard precautions.",
                    }
                ],
                "vocabulary": [
                    {
                        "word": "standard precautions",
                        "definition": "Basic infection prevention steps used with every patient.",
                        "example_sentence": "Nurses use standard precautions during every patient interaction.",
                    }
                ],
                "topic_domains": {
                    "model_passage": "school clinic triage",
                    "assessment_passage": "medical ward wound dressing",                },
                "sub_competencies": [
                    item.model_dump() for item in request.curriculum.sub_competencies
                ],
                "core_concept": request.instructional_design.core_concept,
                "deep_dive_dimensions": ["assessment", "intervention", "evaluation"],
            }
        )

    monkeypatch.setattr(blueprint_module, "call_gemini", fake_call_gemini)

    result = await blueprint_module.generate_blueprint(request)

    assert result.lesson_id == request.lesson_metadata.lesson_code
    assert seen_budgets == [
        blueprint_module.MAX_BLUEPRINT_OUTPUT_TOKENS,
        blueprint_module.MAX_BLUEPRINT_OUTPUT_TOKENS * 2,
    ]
