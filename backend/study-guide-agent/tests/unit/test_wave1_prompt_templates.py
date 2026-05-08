from __future__ import annotations

import json
from pathlib import Path

from app.prompts.templates import (
    intro,
    key_points,
    learning_targets,
    self_assessment,
    vocabulary,
    warmup,
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


def test_wave1_prompt_templates_are_blueprint_driven() -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    intro_prompt = intro.build_prompt(spec=None, blueprint=blueprint, request=request)
    assert blueprint.essential_question in intro_prompt
    assert '"paragraphs": [' in intro_prompt
    assert "Return only JSON." in intro_prompt

    learning_targets_prompt = learning_targets.build_prompt(
        spec=None, blueprint=blueprint, request=request
    )
    assert blueprint.learning_targets[0].objective in learning_targets_prompt
    assert '"success_look_for": "string"' in learning_targets_prompt

    warmup_prompt = warmup.build_prompt(spec=None, blueprint=blueprint, request=request)
    assert blueprint.introduction_hook in warmup_prompt
    assert '"estimated_minutes": 5' in warmup_prompt

    vocabulary_prompt = vocabulary.build_prompt(
        spec=None, blueprint=blueprint, request=request
    )
    assert blueprint.vocabulary[0].word in vocabulary_prompt
    assert '"part_of_speech": "string"' in vocabulary_prompt
    assert "same order" in vocabulary_prompt

    key_points_prompt = key_points.build_prompt(
        spec=None, blueprint=blueprint, request=request
    )
    assert blueprint.sub_competencies[0].label in key_points_prompt
    assert '"sub_competency_id": "string"' in key_points_prompt

    self_assessment_prompt = self_assessment.build_prompt(
        spec=None, blueprint=blueprint, request=request
    )
    assert blueprint.learning_targets[1].objective in self_assessment_prompt
    assert "must match the corresponding learning target objective verbatim" in (
        self_assessment_prompt
    )
    assert '"confidence_levels": [' in self_assessment_prompt
