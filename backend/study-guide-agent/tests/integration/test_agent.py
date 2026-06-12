# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.workflow import Workflow

import app.agent as agent_module
from app.agent import root_agent
from app.types import Blueprint, GenerateRequest, GenerateResponse, ValidationResult


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
                "assessment_passage": "mangrove forest protection article",            },
            "sub_competencies": [
                item.model_dump() for item in request.curriculum.sub_competencies
            ],
            "core_concept": request.instructional_design.core_concept,
            "deep_dive_dimensions": ["entertain", "inform", "persuade"],
            }
    )


class FakeContext:
    def __init__(self) -> None:
        self.node_calls: list[str] = []

    async def run_node(self, node: Any, node_input: Any = None) -> Any:
        node_name_like = getattr(node, "name", type(node).__name__)
        node_name = (
            node_name_like if isinstance(node_name_like, str) else type(node).__name__
        )
        self.node_calls.append(node_name)
        return await node._func(node_input)


def test_root_workflow_is_constructible() -> None:
    """Integration smoke test for the configured workflow entrypoint."""

    session_service = InMemorySessionService()

    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(
        agent=cast(Any, root_agent),
        session_service=session_service,
        app_name="test",
    )

    assert session.id
    assert runner is not None
    assert isinstance(root_agent, Workflow)
    assert root_agent.name == "study_guide_generator"
    assert root_agent.input_schema is GenerateRequest
    assert root_agent.output_schema is GenerateResponse


@pytest.mark.asyncio
async def test_study_guide_workflow_runs_sections_validation_retry_and_render(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    context = FakeContext()

    async def fake_blueprint_node(request_input: GenerateRequest) -> Blueprint:
        assert request_input == request
        return blueprint

    monkeypatch.setattr(agent_module.blueprint_node, "_func", fake_blueprint_node)

    async def fake_generate_intro(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Introduction", "section": "intro", "attempt": 1}

    async def fake_generate_learning_targets(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Learning Targets", "section": "learning_targets"}

    async def fake_generate_warmup(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Warm-Up", "section": "warmup"}

    async def fake_generate_vocabulary(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Vocabulary", "section": "vocabulary"}

    async def fake_generate_key_points(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Key Points", "section": "key_points"}

    async def fake_generate_self_assessment(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Self Assessment", "section": "self_assessment"}

    async def fake_generate_core_explainer(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Core Explainer", "section": "core_explainer"}

    async def fake_generate_subconcept(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sub_competency: Any,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {
            "title": f"Subconcept {sub_competency.id}",
            "section": "subconcept",
            "sub_competency_id": sub_competency.id,
        }

    async def fake_generate_strategy_list(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Strategy List", "section": "strategy_list"}

    async def fake_generate_deep_dive(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Deep Dive", "section": "deep_dive"}

    async def fake_generate_model_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Model Passage", "section": "model_passage"}

    async def fake_generate_assessment_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {
            "title": "Assessment Passage",
            "section": "assessment_passage",
        }

    async def fake_generate_check_in(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["section"] == "model_passage"
        return {"title": "Check In", "section": "check_in"}

    async def fake_generate_assessment_questions(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert assessment_passage["section"] == "assessment_passage"
        return {
            "title": "Assessment Questions",
            "section": "assessment_questions",
        }

    async def fake_generate_step_up(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert assessment_passage["section"] == "assessment_passage"
        assert assessment_questions["section"] == "assessment_questions"
        return {"title": "Step Up", "section": "step_up"}

    async def fake_generate_answer_key(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
        check_in: dict[str, Any],
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
        step_up: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["section"] == "model_passage"
        assert check_in["section"] == "check_in"
        assert assessment_passage["section"] == "assessment_passage"
        assert assessment_questions["section"] == "assessment_questions"
        assert step_up["section"] == "step_up"
        return {"title": "Answer Key", "section": "answer_key"}

    validation_passes = 0

    async def fake_generate_validation(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sections: dict[str, Any],
    ) -> ValidationResult:
        nonlocal validation_passes
        assert request_input == request
        assert blueprint_input == blueprint
        validation_passes += 1
        if validation_passes == 1:
            assert sections["intro"]["attempt"] == 1
            return ValidationResult(
                passed=False,
                failed_sections=["intro"],
                failures={"intro": ["Missing required vocabulary term."]},
                warnings=[],
                best_effort_sections=[],
            )

        assert sections["intro"]["attempt"] == 2
        return ValidationResult(
            passed=True,
            failed_sections=[],
            failures={},
            warnings=[],
            best_effort_sections=[],
        )

    async def fake_call_gemini(**kwargs: Any) -> str:
        assert kwargs["temperature"] == agent_module.TEMP_RETRY
        assert kwargs["context_label"] == "intro_retry"
        assert "Missing required vocabulary term." in kwargs["user_prompt"]
        return json.dumps(
            {
                "title": "Introduction",
                "section": "intro",
                "attempt": 2,
            }
        )

    async def fake_generate_rendered_response(
        blueprint_input: Blueprint,
        sections: dict[str, Any],
        validation: ValidationResult,
    ) -> GenerateResponse:
        assert blueprint_input == blueprint
        assert sections["intro"]["attempt"] == 2
        assert validation.passed is True
        return GenerateResponse.model_validate(
            {
                "success": True,
                "pdf_base64": "cGRm",
                "preview": {"sections": []},
                "validation": validation.model_dump(mode="json"),
                "error": None,
            }
        )

    monkeypatch.setattr(agent_module, "generate_intro", fake_generate_intro)
    monkeypatch.setattr(
        agent_module,
        "generate_learning_targets",
        fake_generate_learning_targets,
    )
    monkeypatch.setattr(agent_module, "generate_warmup", fake_generate_warmup)
    monkeypatch.setattr(agent_module, "generate_vocabulary", fake_generate_vocabulary)
    monkeypatch.setattr(agent_module, "generate_key_points", fake_generate_key_points)
    monkeypatch.setattr(
        agent_module,
        "generate_self_assessment",
        fake_generate_self_assessment,
    )
    monkeypatch.setattr(
        agent_module,
        "generate_core_explainer",
        fake_generate_core_explainer,
    )
    monkeypatch.setattr(agent_module, "generate_subconcept", fake_generate_subconcept)
    monkeypatch.setattr(
        agent_module,
        "generate_strategy_list",
        fake_generate_strategy_list,
    )
    monkeypatch.setattr(agent_module, "generate_deep_dive", fake_generate_deep_dive)
    monkeypatch.setattr(
        agent_module,
        "generate_model_passage",
        fake_generate_model_passage,
    )
    monkeypatch.setattr(
        agent_module,
        "generate_assessment_passage",
        fake_generate_assessment_passage,
    )
    monkeypatch.setattr(agent_module, "generate_check_in", fake_generate_check_in)
    monkeypatch.setattr(
        agent_module,
        "generate_assessment_questions",
        fake_generate_assessment_questions,
    )
    monkeypatch.setattr(agent_module, "generate_step_up", fake_generate_step_up)
    monkeypatch.setattr(agent_module, "generate_answer_key", fake_generate_answer_key)
    monkeypatch.setattr(agent_module, "generate_validation", fake_generate_validation)
    monkeypatch.setattr(agent_module, "call_gemini", fake_call_gemini)
    monkeypatch.setattr(
        agent_module,
        "generate_rendered_response",
        fake_generate_rendered_response,
    )

    result = await cast(Any, agent_module.study_guide_workflow)._func(context, request)

    assert result.success is True
    assert validation_passes == 2
    assert context.node_calls[0] == cast(Any, agent_module.blueprint_node).name
    assert any(
        node_name.startswith("retry_intro_1") for node_name in context.node_calls
    )
    assert context.node_calls[-1] == cast(Any, agent_module.render_workflow_node).name


@pytest.mark.asyncio
async def test_study_guide_workflow_normalizes_answer_key_before_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    context = FakeContext()

    async def fake_blueprint_node(request_input: GenerateRequest) -> Blueprint:
        assert request_input == request
        return blueprint

    monkeypatch.setattr(agent_module.blueprint_node, "_func", fake_blueprint_node)

    async def fake_generate_simple_section(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Section"}

    async def fake_generate_subconcept(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sub_competency: Any,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": f"Subconcept {sub_competency.id}"}

    async def fake_generate_model_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Model Passage", "section": "model_passage"}

    async def fake_generate_assessment_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {
            "title": "Assessment Passage",
            "topic_domain": "mangrove forest protection article",
            "genre": "informational",
            "passage": [
                "Mangrove forests protect coastlines from strong waves.",
                "They help both people and wildlife stay safe.",
            ],
            "evidence_clues": ["protect coastlines", "stay safe"],
            "answerability_note": "",
        }

    async def fake_generate_check_in(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["section"] == "model_passage"
        return {
            "title": "Check In",
            "questions": [
                {
                    "number": 1,
                    "question": "What clues show the author's purpose?",
                    "evidence_hint": "Look at the encouraging language.",
                    "expected_response_type": "short_response",
                }
            ],
        }

    async def fake_generate_assessment_questions(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert assessment_passage["title"] == "Assessment Passage"
        return {
            "title": "Assessment Questions",
            "passage_title": "Assessment Passage",
            "questions": [
                {
                    "number": 1,
                    "question": "What is the author's purpose in this article?",
                    "expected_response_type": "short_response",
                    "evidence_hint": "Look for a phrase that explains why mangroves matter.",
                }
            ],
        }

    async def fake_generate_step_up(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert assessment_passage["title"] == "Assessment Passage"
        assert assessment_questions["title"] == "Assessment Questions"
        return {
            "title": "Step Up",
            "challenge_prompt": "Use evidence from the passage to explain the author's purpose.",
            "required_evidence": ["protect coastlines"],
            "success_criteria": ["Answers use evidence from the passage."],
        }

    async def fake_generate_answer_key(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
        check_in: dict[str, Any],
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
        step_up: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["title"] == "Model Passage"
        assert check_in["title"] == "Check In"
        assert assessment_passage["title"] == "Assessment Passage"
        assert assessment_questions["title"] == "Assessment Questions"
        assert step_up["title"] == "Step Up"
        # Real generate_answer_key always normalizes before returning.
        # This fake returns the already-normalized form.
        return {
            "title": "Answer Key",
            "check_in_answers": [
                {
                    "question_number": 1,
                    "question": "What clues show the author's purpose?",
                    "possible_answer": "The descriptive details guide the reader toward the main idea.",
                    "evidence_quote": "N/A",
                }
            ],
            "assessment_answers": [
                {
                    "question_number": 1,
                    "question": "What is the author's purpose in this article?",
                    "possible_answer": "The author wants readers to care because the mangrove roots keep every shoreline family safe during strong storms.",
                    "evidence_quote": '"protect coastlines"',
                }
            ],
            "step_up_answer": {
                "challenge_response": "The passage explains why the evidence matters.",
                "required_evidence": ["protect coastlines"],
            },
            "teacher_note": "Accept concise answers that explain the purpose and cite evidence.",
        }

    async def fake_generate_validation(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sections: dict[str, Any],
    ) -> ValidationResult:
        assert request_input == request
        assert blueprint_input == blueprint
        assert sections["answer_key"]["check_in_answers"][0]["evidence_quote"] == "N/A"
        assert sections["answer_key"]["assessment_answers"] == [
            {
                "question_number": 1,
                "question": "What is the author's purpose in this article?",
                "possible_answer": "The author wants readers to care because the mangrove roots keep every shoreline family safe during strong storms.",
                "evidence_quote": '"protect coastlines"',
            }
        ]
        return ValidationResult(
            passed=True,
            failed_sections=[],
            failures={},
            warnings=[],
            best_effort_sections=[],
        )

    async def fake_generate_rendered_response(
        blueprint_input: Blueprint,
        sections: dict[str, Any],
        validation: ValidationResult,
    ) -> GenerateResponse:
        assert blueprint_input == blueprint
        assert validation.passed is True
        return GenerateResponse.model_validate(
            {
                "success": True,
                "pdf_base64": "cGRm",
                "preview": {"sections": []},
                "validation": validation.model_dump(mode="json"),
                "error": None,
            }
        )

    monkeypatch.setattr(agent_module, "generate_intro", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_learning_targets", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_warmup", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_vocabulary", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_key_points", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_self_assessment", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_core_explainer", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_subconcept", fake_generate_subconcept)
    monkeypatch.setattr(
        agent_module, "generate_strategy_list", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_deep_dive", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_model_passage", fake_generate_model_passage
    )
    monkeypatch.setattr(
        agent_module, "generate_assessment_passage", fake_generate_assessment_passage
    )
    monkeypatch.setattr(agent_module, "generate_check_in", fake_generate_check_in)
    monkeypatch.setattr(
        agent_module,
        "generate_assessment_questions",
        fake_generate_assessment_questions,
    )
    monkeypatch.setattr(agent_module, "generate_step_up", fake_generate_step_up)
    monkeypatch.setattr(agent_module, "generate_answer_key", fake_generate_answer_key)
    monkeypatch.setattr(agent_module, "generate_validation", fake_generate_validation)
    monkeypatch.setattr(
        agent_module, "generate_rendered_response", fake_generate_rendered_response
    )

    result = await cast(Any, agent_module.study_guide_workflow)._func(context, request)

    assert result.success is True


@pytest.mark.asyncio
async def test_study_guide_workflow_refreshes_downstream_sections_after_assessment_passage_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    context = FakeContext()

    async def fake_blueprint_node(request_input: GenerateRequest) -> Blueprint:
        assert request_input == request
        return blueprint

    monkeypatch.setattr(agent_module.blueprint_node, "_func", fake_blueprint_node)
    monkeypatch.setattr(
        agent_module, "normalize_answer_key_payload", lambda *args: args[0]
    )

    async def fake_generate_simple_section(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Section"}

    async def fake_generate_subconcept(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sub_competency: Any,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": f"Subconcept {sub_competency.id}"}

    async def fake_generate_model_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Model Passage", "section": "model_passage"}

    async def fake_generate_assessment_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {
            "title": "Assessment Passage",
            "section": "assessment_passage",
            "attempt": 1,
        }

    async def fake_generate_check_in(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["section"] == "model_passage"
        return {"title": "Check In", "section": "check_in"}

    async def fake_generate_assessment_questions(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {
            "title": "Assessment Questions",
            "section": "assessment_questions",
            "source_attempt": assessment_passage["attempt"],
        }

    async def fake_generate_step_up(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {
            "title": "Step Up",
            "section": "step_up",
            "source_attempt": assessment_passage["attempt"],
            "question_attempt": assessment_questions["source_attempt"],
        }

    async def fake_generate_answer_key(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
        check_in: dict[str, Any],
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
        step_up: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["section"] == "model_passage"
        assert check_in["section"] == "check_in"
        return {
            "title": "Answer Key",
            "section": "answer_key",
            "passage_attempt": assessment_passage["attempt"],
            "question_attempt": assessment_questions["source_attempt"],
            "step_up_attempt": step_up["source_attempt"],
        }

    validation_passes = 0

    async def fake_generate_validation(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sections: dict[str, Any],
    ) -> ValidationResult:
        nonlocal validation_passes
        assert request_input == request
        assert blueprint_input == blueprint
        validation_passes += 1
        if validation_passes == 1:
            assert sections["assessment_passage"]["attempt"] == 1
            assert sections["assessment_questions"]["source_attempt"] == 1
            assert sections["step_up"]["source_attempt"] == 1
            assert sections["answer_key"]["passage_attempt"] == 1
            return ValidationResult(
                passed=False,
                failed_sections=["assessment_passage"],
                failures={"assessment_passage": ["Passage needs revision."]},
                warnings=[],
                best_effort_sections=[],
            )

        assert sections["assessment_passage"]["attempt"] == 2
        assert sections["assessment_questions"]["source_attempt"] == 2
        assert sections["step_up"]["source_attempt"] == 2
        assert sections["step_up"]["question_attempt"] == 2
        assert sections["answer_key"]["passage_attempt"] == 2
        assert sections["answer_key"]["question_attempt"] == 2
        assert sections["answer_key"]["step_up_attempt"] == 2
        return ValidationResult(
            passed=True,
            failed_sections=[],
            failures={},
            warnings=[],
            best_effort_sections=[],
        )

    async def fake_call_gemini(**kwargs: Any) -> str:
        assert kwargs["temperature"] == agent_module.TEMP_RETRY
        assert kwargs["context_label"] == "assessment_passage_retry"
        assert "Passage needs revision." in kwargs["user_prompt"]
        return json.dumps(
            {
                "title": "Assessment Passage",
                "section": "assessment_passage",
                "attempt": 2,
            }
        )

    async def fake_generate_rendered_response(
        blueprint_input: Blueprint,
        sections: dict[str, Any],
        validation: ValidationResult,
    ) -> GenerateResponse:
        assert blueprint_input == blueprint
        assert validation.passed is True
        assert sections["answer_key"]["passage_attempt"] == 2
        return GenerateResponse.model_validate(
            {
                "success": True,
                "pdf_base64": "cGRm",
                "preview": {"sections": []},
                "validation": validation.model_dump(mode="json"),
                "error": None,
            }
        )

    monkeypatch.setattr(agent_module, "generate_intro", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_learning_targets", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_warmup", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_vocabulary", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_key_points", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_self_assessment", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_core_explainer", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_subconcept", fake_generate_subconcept)
    monkeypatch.setattr(
        agent_module, "generate_strategy_list", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_deep_dive", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_model_passage", fake_generate_model_passage
    )
    monkeypatch.setattr(
        agent_module, "generate_assessment_passage", fake_generate_assessment_passage
    )
    monkeypatch.setattr(agent_module, "generate_check_in", fake_generate_check_in)
    monkeypatch.setattr(
        agent_module,
        "generate_assessment_questions",
        fake_generate_assessment_questions,
    )
    monkeypatch.setattr(agent_module, "generate_step_up", fake_generate_step_up)
    monkeypatch.setattr(agent_module, "generate_answer_key", fake_generate_answer_key)
    monkeypatch.setattr(agent_module, "generate_validation", fake_generate_validation)
    monkeypatch.setattr(agent_module, "call_gemini", fake_call_gemini)
    monkeypatch.setattr(
        agent_module, "generate_rendered_response", fake_generate_rendered_response
    )

    result = await cast(Any, agent_module.study_guide_workflow)._func(context, request)

    assert result.success is True
    assert validation_passes == 2


@pytest.mark.asyncio
async def test_study_guide_workflow_refreshes_check_in_and_answer_key_after_model_passage_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    context = FakeContext()

    async def fake_blueprint_node(request_input: GenerateRequest) -> Blueprint:
        assert request_input == request
        return blueprint

    monkeypatch.setattr(agent_module.blueprint_node, "_func", fake_blueprint_node)
    monkeypatch.setattr(
        agent_module, "normalize_answer_key_payload", lambda *args: args[0]
    )

    async def fake_generate_simple_section(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Section"}

    async def fake_generate_subconcept(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sub_competency: Any,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": f"Subconcept {sub_competency.id}"}

    async def fake_generate_model_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Model Passage", "section": "model_passage", "attempt": 1}

    async def fake_generate_assessment_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Assessment Passage", "section": "assessment_passage"}

    async def fake_generate_check_in(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {
            "title": "Check In",
            "section": "check_in",
            "source_attempt": model_passage["attempt"],
        }

    async def fake_generate_assessment_questions(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Assessment Questions", "section": "assessment_questions"}

    async def fake_generate_step_up(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Step Up", "section": "step_up"}

    async def fake_generate_answer_key(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
        check_in: dict[str, Any],
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
        step_up: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert assessment_passage["section"] == "assessment_passage"
        assert assessment_questions["section"] == "assessment_questions"
        assert step_up["section"] == "step_up"
        return {
            "title": "Answer Key",
            "section": "answer_key",
            "model_attempt": model_passage["attempt"],
            "check_in_attempt": check_in["source_attempt"],
        }

    validation_passes = 0

    async def fake_generate_validation(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sections: dict[str, Any],
    ) -> ValidationResult:
        nonlocal validation_passes
        assert request_input == request
        assert blueprint_input == blueprint
        validation_passes += 1
        if validation_passes == 1:
            assert sections["model_passage"]["attempt"] == 1
            assert sections["check_in"]["source_attempt"] == 1
            assert sections["answer_key"]["model_attempt"] == 1
            return ValidationResult(
                passed=False,
                failed_sections=["model_passage"],
                failures={"model_passage": ["Model passage needs revision."]},
                warnings=[],
                best_effort_sections=[],
            )

        assert sections["model_passage"]["attempt"] == 2
        assert sections["check_in"]["source_attempt"] == 2
        assert sections["answer_key"]["model_attempt"] == 2
        assert sections["answer_key"]["check_in_attempt"] == 2
        return ValidationResult(
            passed=True,
            failed_sections=[],
            failures={},
            warnings=[],
            best_effort_sections=[],
        )

    async def fake_call_gemini(**kwargs: Any) -> str:
        assert kwargs["temperature"] == agent_module.TEMP_RETRY
        assert kwargs["context_label"] == "model_passage_retry"
        assert "Model passage needs revision." in kwargs["user_prompt"]
        return json.dumps(
            {
                "title": "Model Passage",
                "section": "model_passage",
                "attempt": 2,
            }
        )

    async def fake_generate_rendered_response(
        blueprint_input: Blueprint,
        sections: dict[str, Any],
        validation: ValidationResult,
    ) -> GenerateResponse:
        assert blueprint_input == blueprint
        assert validation.passed is True
        assert sections["answer_key"]["check_in_attempt"] == 2
        return GenerateResponse.model_validate(
            {
                "success": True,
                "pdf_base64": "cGRm",
                "preview": {"sections": []},
                "validation": validation.model_dump(mode="json"),
                "error": None,
            }
        )

    monkeypatch.setattr(agent_module, "generate_intro", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_learning_targets", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_warmup", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_vocabulary", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_key_points", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_self_assessment", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_core_explainer", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_subconcept", fake_generate_subconcept)
    monkeypatch.setattr(
        agent_module, "generate_strategy_list", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_deep_dive", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_model_passage", fake_generate_model_passage
    )
    monkeypatch.setattr(
        agent_module, "generate_assessment_passage", fake_generate_assessment_passage
    )
    monkeypatch.setattr(agent_module, "generate_check_in", fake_generate_check_in)
    monkeypatch.setattr(
        agent_module,
        "generate_assessment_questions",
        fake_generate_assessment_questions,
    )
    monkeypatch.setattr(agent_module, "generate_step_up", fake_generate_step_up)
    monkeypatch.setattr(agent_module, "generate_answer_key", fake_generate_answer_key)
    monkeypatch.setattr(agent_module, "generate_validation", fake_generate_validation)
    monkeypatch.setattr(agent_module, "call_gemini", fake_call_gemini)
    monkeypatch.setattr(
        agent_module, "generate_rendered_response", fake_generate_rendered_response
    )

    result = await cast(Any, agent_module.study_guide_workflow)._func(context, request)

    assert result.success is True
    assert validation_passes == 2


@pytest.mark.asyncio
async def test_study_guide_workflow_refreshes_answer_key_after_check_in_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    context = FakeContext()

    async def fake_blueprint_node(request_input: GenerateRequest) -> Blueprint:
        assert request_input == request
        return blueprint

    monkeypatch.setattr(agent_module.blueprint_node, "_func", fake_blueprint_node)
    monkeypatch.setattr(
        agent_module, "normalize_answer_key_payload", lambda *args: args[0]
    )

    async def fake_generate_simple_section(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Section"}

    async def fake_generate_subconcept(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sub_competency: Any,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": f"Subconcept {sub_competency.id}"}

    async def fake_generate_model_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Model Passage", "section": "model_passage"}

    async def fake_generate_assessment_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Assessment Passage", "section": "assessment_passage"}

    async def fake_generate_check_in(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["section"] == "model_passage"
        return {"title": "Check In", "section": "check_in", "attempt": 1}

    async def fake_generate_assessment_questions(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Assessment Questions", "section": "assessment_questions"}

    async def fake_generate_step_up(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Step Up", "section": "step_up"}

    async def fake_generate_answer_key(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
        check_in: dict[str, Any],
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
        step_up: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["section"] == "model_passage"
        assert assessment_passage["section"] == "assessment_passage"
        assert assessment_questions["section"] == "assessment_questions"
        assert step_up["section"] == "step_up"
        return {
            "title": "Answer Key",
            "section": "answer_key",
            "check_in_attempt": check_in["attempt"],
        }

    validation_passes = 0

    async def fake_generate_validation(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sections: dict[str, Any],
    ) -> ValidationResult:
        nonlocal validation_passes
        assert request_input == request
        assert blueprint_input == blueprint
        validation_passes += 1
        if validation_passes == 1:
            assert sections["check_in"]["attempt"] == 1
            assert sections["answer_key"]["check_in_attempt"] == 1
            return ValidationResult(
                passed=False,
                failed_sections=["check_in"],
                failures={"check_in": ["Check-in needs revision."]},
                warnings=[],
                best_effort_sections=[],
            )

        assert sections["check_in"]["attempt"] == 2
        assert sections["answer_key"]["check_in_attempt"] == 2
        return ValidationResult(
            passed=True,
            failed_sections=[],
            failures={},
            warnings=[],
            best_effort_sections=[],
        )

    async def fake_call_gemini(**kwargs: Any) -> str:
        assert kwargs["temperature"] == agent_module.TEMP_RETRY
        assert kwargs["context_label"] == "check_in_retry"
        assert "Check-in needs revision." in kwargs["user_prompt"]
        return json.dumps(
            {
                "title": "Check In",
                "section": "check_in",
                "attempt": 2,
            }
        )

    async def fake_generate_rendered_response(
        blueprint_input: Blueprint,
        sections: dict[str, Any],
        validation: ValidationResult,
    ) -> GenerateResponse:
        assert blueprint_input == blueprint
        assert validation.passed is True
        assert sections["answer_key"]["check_in_attempt"] == 2
        return GenerateResponse.model_validate(
            {
                "success": True,
                "pdf_base64": "cGRm",
                "preview": {"sections": []},
                "validation": validation.model_dump(mode="json"),
                "error": None,
            }
        )

    monkeypatch.setattr(agent_module, "generate_intro", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_learning_targets", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_warmup", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_vocabulary", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_key_points", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_self_assessment", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_core_explainer", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_subconcept", fake_generate_subconcept)
    monkeypatch.setattr(
        agent_module, "generate_strategy_list", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_deep_dive", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_model_passage", fake_generate_model_passage
    )
    monkeypatch.setattr(
        agent_module, "generate_assessment_passage", fake_generate_assessment_passage
    )
    monkeypatch.setattr(agent_module, "generate_check_in", fake_generate_check_in)
    monkeypatch.setattr(
        agent_module,
        "generate_assessment_questions",
        fake_generate_assessment_questions,
    )
    monkeypatch.setattr(agent_module, "generate_step_up", fake_generate_step_up)
    monkeypatch.setattr(agent_module, "generate_answer_key", fake_generate_answer_key)
    monkeypatch.setattr(agent_module, "generate_validation", fake_generate_validation)
    monkeypatch.setattr(agent_module, "call_gemini", fake_call_gemini)
    monkeypatch.setattr(
        agent_module, "generate_rendered_response", fake_generate_rendered_response
    )

    result = await cast(Any, agent_module.study_guide_workflow)._func(context, request)

    assert result.success is True
    assert validation_passes == 2
    assert result.validation.failed_sections == []


@pytest.mark.asyncio
async def test_study_guide_workflow_skips_stale_downstream_retries_after_assessment_passage_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    context = FakeContext()

    async def fake_blueprint_node(request_input: GenerateRequest) -> Blueprint:
        assert request_input == request
        return blueprint

    monkeypatch.setattr(agent_module.blueprint_node, "_func", fake_blueprint_node)
    monkeypatch.setattr(
        agent_module, "normalize_answer_key_payload", lambda *args: args[0]
    )

    async def fake_generate_simple_section(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Section"}

    async def fake_generate_subconcept(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sub_competency: Any,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": f"Subconcept {sub_competency.id}"}

    async def fake_generate_model_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {"title": "Model Passage", "section": "model_passage"}

    async def fake_generate_assessment_passage(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        return {
            "title": "Assessment Passage",
            "section": "assessment_passage",
            "attempt": 1,
        }

    async def fake_generate_check_in(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["section"] == "model_passage"
        return {"title": "Check In", "section": "check_in"}

    assessment_question_attempts: list[int] = []

    async def fake_generate_assessment_questions(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assessment_question_attempts.append(assessment_passage["attempt"])
        return {
            "title": "Assessment Questions",
            "section": "assessment_questions",
            "attempt": assessment_passage["attempt"],
        }

    step_up_attempts: list[int] = []

    async def fake_generate_step_up(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert assessment_passage["attempt"] == assessment_questions["attempt"]
        step_up_attempts.append(assessment_questions["attempt"])
        return {
            "title": "Step Up",
            "section": "step_up",
            "attempt": assessment_questions["attempt"],
        }

    answer_key_attempts: list[tuple[int, int, int]] = []

    async def fake_generate_answer_key(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        model_passage: dict[str, Any],
        check_in: dict[str, Any],
        assessment_passage: dict[str, Any],
        assessment_questions: dict[str, Any],
        step_up: dict[str, Any],
    ) -> dict[str, Any]:
        assert request_input == request
        assert blueprint_input == blueprint
        assert model_passage["section"] == "model_passage"
        assert check_in["section"] == "check_in"
        answer_key_attempts.append(
            (
                assessment_passage["attempt"],
                assessment_questions["attempt"],
                step_up["attempt"],
            )
        )
        return {
            "title": "Answer Key",
            "section": "answer_key",
            "attempt": assessment_questions["attempt"],
        }

    validation_passes = 0

    async def fake_generate_validation(
        request_input: GenerateRequest,
        blueprint_input: Blueprint,
        sections: dict[str, Any],
    ) -> ValidationResult:
        nonlocal validation_passes
        assert request_input == request
        assert blueprint_input == blueprint
        validation_passes += 1
        if validation_passes == 1:
            assert sections["assessment_passage"]["attempt"] == 1
            assert sections["assessment_questions"]["attempt"] == 1
            assert sections["step_up"]["attempt"] == 1
            assert sections["answer_key"]["attempt"] == 1
            return ValidationResult(
                passed=False,
                failed_sections=[
                    "assessment_passage",
                    "assessment_questions",
                    "step_up",
                    "answer_key",
                ],
                failures={
                    "assessment_passage": ["Passage needs revision."],
                    "assessment_questions": ["Questions need revision."],
                    "step_up": ["Step-up needs revision."],
                    "answer_key": ["Answer key needs revision."],
                },
                warnings=[],
                best_effort_sections=[],
            )

        assert sections["assessment_passage"]["attempt"] == 2
        assert sections["assessment_questions"]["attempt"] == 2
        assert sections["step_up"]["attempt"] == 2
        assert sections["answer_key"]["attempt"] == 2
        return ValidationResult(
            passed=True,
            failed_sections=[],
            failures={},
            warnings=[],
            best_effort_sections=[],
        )

    async def fake_call_gemini(**kwargs: Any) -> str:
        assert kwargs["temperature"] == agent_module.TEMP_RETRY
        assert kwargs["context_label"] == "assessment_passage_retry"
        assert "Passage needs revision." in kwargs["user_prompt"]
        return json.dumps(
            {
                "title": "Assessment Passage",
                "section": "assessment_passage",
                "attempt": 2,
            }
        )

    async def fake_generate_rendered_response(
        blueprint_input: Blueprint,
        sections: dict[str, Any],
        validation: ValidationResult,
    ) -> GenerateResponse:
        assert blueprint_input == blueprint
        assert validation.passed is True
        assert sections["answer_key"]["attempt"] == 2
        return GenerateResponse.model_validate(
            {
                "success": True,
                "pdf_base64": "cGRm",
                "preview": {"sections": []},
                "validation": validation.model_dump(mode="json"),
                "error": None,
            }
        )

    monkeypatch.setattr(agent_module, "generate_intro", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_learning_targets", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_warmup", fake_generate_simple_section)
    monkeypatch.setattr(
        agent_module, "generate_vocabulary", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_key_points", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_self_assessment", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_core_explainer", fake_generate_simple_section
    )
    monkeypatch.setattr(agent_module, "generate_subconcept", fake_generate_subconcept)
    monkeypatch.setattr(
        agent_module, "generate_strategy_list", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_deep_dive", fake_generate_simple_section
    )
    monkeypatch.setattr(
        agent_module, "generate_model_passage", fake_generate_model_passage
    )
    monkeypatch.setattr(
        agent_module, "generate_assessment_passage", fake_generate_assessment_passage
    )
    monkeypatch.setattr(agent_module, "generate_check_in", fake_generate_check_in)
    monkeypatch.setattr(
        agent_module,
        "generate_assessment_questions",
        fake_generate_assessment_questions,
    )
    monkeypatch.setattr(agent_module, "generate_step_up", fake_generate_step_up)
    monkeypatch.setattr(agent_module, "generate_answer_key", fake_generate_answer_key)
    monkeypatch.setattr(agent_module, "generate_validation", fake_generate_validation)
    monkeypatch.setattr(agent_module, "call_gemini", fake_call_gemini)
    monkeypatch.setattr(
        agent_module, "generate_rendered_response", fake_generate_rendered_response
    )

    result = await cast(Any, agent_module.study_guide_workflow)._func(context, request)

    retry_calls = [
        node_name for node_name in context.node_calls if node_name.startswith("retry_")
    ]
    assert retry_calls == ["retry_assessment_passage_1"]
    assert assessment_question_attempts == [1, 2]
    assert step_up_attempts == [1, 2]
    assert answer_key_attempts == [(1, 1, 1), (2, 2, 2)]
    assert validation_passes == 2
    assert result.validation.failed_sections == []
