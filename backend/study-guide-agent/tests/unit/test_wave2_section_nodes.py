from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.nodes.sections as sections_module
from app.nodes.sections import assessment_passage as assessment_passage_module
from app.nodes.sections import core_explainer as core_explainer_module
from app.nodes.sections import deep_dive as deep_dive_module
from app.nodes.sections import model_passage as model_passage_module
from app.nodes.sections import strategy_list as strategy_list_module
from app.nodes.sections import subconcept as subconcept_module
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


@pytest.mark.asyncio
async def test_wave2_section_nodes_generate_structured_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    first_subcompetency = blueprint.sub_competencies[0]

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

        expected_fragments = {
            "core_explainer": [blueprint.core_concept, first_subcompetency.label],
            "subconcept": [first_subcompetency.id, first_subcompetency.label],
            "strategy_list": [blueprint.essential_question],
            "deep_dive": [blueprint.topic_domains.entertain_example],
            "model_passage": [blueprint.topic_domains.model_passage],
            "assessment_passage": [
                blueprint.topic_domains.assessment_passage,
                blueprint.topic_domains.model_passage,
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

    modules = [
        (core_explainer_module.generate_core_explainer, "core_explainer", []),
        (
            subconcept_module.generate_subconcept,
            "subconcept",
            [first_subcompetency],
        ),
        (strategy_list_module.generate_strategy_list, "strategy_list", []),
        (deep_dive_module.generate_deep_dive, "deep_dive", []),
        (model_passage_module.generate_model_passage, "model_passage", []),
        (
            assessment_passage_module.generate_assessment_passage,
            "assessment_passage",
            [],
        ),
    ]

    for generator, expected_label, extra_args in modules:
        result = await generator(request, blueprint, *extra_args)

        assert result["context_label"] == expected_label
        assert result["items"] == [request.lesson_metadata.lesson_code]


@pytest.mark.asyncio
async def test_wave2_section_nodes_raise_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return "not-json"

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    with pytest.raises(
        RuntimeError, match="Failed to parse model_passage response as JSON"
    ):
        await model_passage_module.generate_model_passage(request, blueprint)


@pytest.mark.asyncio
async def test_wave2_section_nodes_repair_lone_backslashes_in_json_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        valid_payload = json.dumps(
            {
                "title": "Model Passage",
                "topic_domain": "fraction tiles",
                "genre": "explanation",
                "passage": ["Compare 1/2 and \\frac{3}{4} using a common denominator."],
                "text_features": ["comparison words"],
                "evidence_focus": "The comparison sentence.",
            }
        )
        return valid_payload.replace("\\\\frac", "\\frac")

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await model_passage_module.generate_model_passage(request, blueprint)

    assert result["passage"] == [
        "Compare 1/2 and \\frac{3}{4} using a common denominator."
    ]
