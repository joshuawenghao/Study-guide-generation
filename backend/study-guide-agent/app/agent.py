# ruff: noqa: E402

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, cast

from pydantic import BaseModel, Field

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk import Context
from google.adk.apps import App
from google.adk.workflow import Workflow, node

from app.nodes.base import TEMP_RETRY, call_gemini
from app.nodes.blueprint import blueprint_node
from app.nodes.renderer import generate_rendered_response
from app.nodes.sections import _parse_section_response
from app.nodes.sections.answer_key import (
    generate_answer_key,
    normalize_answer_key_payload,
)
from app.nodes.sections.assessment_passage import generate_assessment_passage
from app.nodes.sections.assessment_questions import generate_assessment_questions
from app.nodes.sections.check_in import generate_check_in
from app.nodes.sections.core_explainer import generate_core_explainer
from app.nodes.sections.deep_dive import generate_deep_dive
from app.nodes.sections.intro import generate_intro
from app.nodes.sections.key_points import generate_key_points
from app.nodes.sections.learning_targets import generate_learning_targets
from app.nodes.sections.model_passage import generate_model_passage
from app.nodes.sections.self_assessment import generate_self_assessment
from app.nodes.sections.step_up import generate_step_up
from app.nodes.sections.strategy_list import generate_strategy_list
from app.nodes.sections.subconcept import generate_subconcept
from app.nodes.sections.vocabulary import generate_vocabulary
from app.nodes.sections.warmup import generate_warmup
from app.nodes.validator import generate_validation
from app.prompts.system_prompt import build_system_prompt
from app.prompts.templates.answer_key import build_prompt as build_answer_key_prompt
from app.prompts.templates.assessment_passage import (
    build_prompt as build_assessment_passage_prompt,
)
from app.prompts.templates.assessment_questions import (
    build_prompt as build_assessment_questions_prompt,
)
from app.prompts.templates.check_in import build_prompt as build_check_in_prompt
from app.prompts.templates.core_explainer import (
    build_prompt as build_core_explainer_prompt,
)
from app.prompts.templates.deep_dive import build_prompt as build_deep_dive_prompt
from app.prompts.templates.intro import build_prompt as build_intro_prompt
from app.prompts.templates.key_points import build_prompt as build_key_points_prompt
from app.prompts.templates.learning_targets import (
    build_prompt as build_learning_targets_prompt,
)
from app.prompts.templates.model_passage import (
    build_prompt as build_model_passage_prompt,
)
from app.prompts.templates.self_assessment import (
    build_prompt as build_self_assessment_prompt,
)
from app.prompts.templates.step_up import build_prompt as build_step_up_prompt
from app.prompts.templates.strategy_list import (
    build_prompt as build_strategy_list_prompt,
)
from app.prompts.templates.subconcept import build_prompt as build_subconcept_prompt
from app.prompts.templates.vocabulary import build_prompt as build_vocabulary_prompt
from app.prompts.templates.warmup import build_prompt as build_warmup_prompt
from app.types import (
    Blueprint,
    GenerateRequest,
    GenerateResponse,
    SubCompetency,
    ValidationResult,
)


class SectionNodeInput(BaseModel):
    request: GenerateRequest
    blueprint: Blueprint


class SubconceptNodeInput(SectionNodeInput):
    request: GenerateRequest
    blueprint: Blueprint
    sub_competency: SubCompetency


class CheckInNodeInput(SectionNodeInput):
    request: GenerateRequest
    blueprint: Blueprint
    model_passage: dict[str, Any]


class AssessmentQuestionsNodeInput(SectionNodeInput):
    request: GenerateRequest
    blueprint: Blueprint
    assessment_passage: dict[str, Any]


class StepUpNodeInput(AssessmentQuestionsNodeInput):
    request: GenerateRequest
    blueprint: Blueprint
    assessment_passage: dict[str, Any]
    assessment_questions: dict[str, Any]


class AnswerKeyNodeInput(AssessmentQuestionsNodeInput):
    request: GenerateRequest
    blueprint: Blueprint
    model_passage: dict[str, Any]
    assessment_passage: dict[str, Any]
    check_in: dict[str, Any]
    assessment_questions: dict[str, Any]
    step_up: dict[str, Any]


class ValidationNodeInput(BaseModel):
    request: GenerateRequest
    blueprint: Blueprint
    sections: dict[str, Any]


class RenderNodeInput(BaseModel):
    blueprint: Blueprint
    sections: dict[str, Any]
    validation: ValidationResult


class RetryNodeInput(ValidationNodeInput):
    section_key: str
    failure_messages: list[str] = Field(default_factory=list)


PromptBuilder = Callable[[Any, Blueprint, GenerateRequest], str]


def _with_retry_guidance(prompt: str, failure_messages: list[str]) -> str:
    guidance_lines = [
        "Revise this section to satisfy the validator feedback below.",
        "Keep the same JSON schema and return JSON only.",
        "Validation failures:",
        *[f"- {message}" for message in failure_messages],
    ]
    return f"{prompt}\n\n" + "\n".join(guidance_lines)


def _retry_prompt_builder(
    section_key: str,
    blueprint: Blueprint,
    request: GenerateRequest,
    sections: dict[str, Any],
) -> tuple[PromptBuilder, Any]:
    if section_key == "intro":
        return build_intro_prompt, None
    if section_key == "learning_targets":
        return build_learning_targets_prompt, None
    if section_key == "warmup":
        return build_warmup_prompt, None
    if section_key == "vocabulary":
        return build_vocabulary_prompt, None
    if section_key == "core_explainer":
        return build_core_explainer_prompt, None
    if section_key == "strategy_list":
        return build_strategy_list_prompt, None
    if section_key == "deep_dive":
        return build_deep_dive_prompt, None
    if section_key == "model_passage":
        return build_model_passage_prompt, None
    if section_key == "check_in":
        return build_check_in_prompt, sections["model_passage"]
    if section_key == "key_points":
        return build_key_points_prompt, None
    if section_key == "assessment_passage":
        return build_assessment_passage_prompt, None
    if section_key == "assessment_questions":
        return build_assessment_questions_prompt, sections["assessment_passage"]
    if section_key == "step_up":
        return build_step_up_prompt, {
            "assessment_passage": sections["assessment_passage"],
            "assessment_questions": sections["assessment_questions"],
        }
    if section_key == "self_assessment":
        return build_self_assessment_prompt, None
    if section_key == "answer_key":
        return build_answer_key_prompt, {
            "model_passage": sections["model_passage"],
            "check_in": sections["check_in"],
            "assessment_passage": sections["assessment_passage"],
            "assessment_questions": sections["assessment_questions"],
            "step_up": sections["step_up"],
        }
    raise ValueError(f"Unsupported retry section: {section_key}")


async def _generate_retry_payload(node_input: RetryNodeInput) -> Any:
    system_prompt = build_system_prompt(node_input.request)

    if node_input.section_key == "subconcept":

        async def retry_subconcept(sub_competency: SubCompetency) -> dict[str, Any]:
            prompt = build_subconcept_prompt(
                sub_competency,
                node_input.blueprint,
                node_input.request,
            )
            response_text = await call_gemini(
                system_prompt=system_prompt,
                user_prompt=_with_retry_guidance(
                    prompt,
                    node_input.failure_messages,
                ),
                temperature=TEMP_RETRY,
                context_label="subconcept_retry",
            )
            return _parse_section_response(response_text, "subconcept")

        return await asyncio.gather(
            *[
                retry_subconcept(sub_competency)
                for sub_competency in node_input.blueprint.sub_competencies
            ]
        )

    prompt_builder, spec = _retry_prompt_builder(
        node_input.section_key,
        node_input.blueprint,
        node_input.request,
        node_input.sections,
    )
    response_text = await call_gemini(
        system_prompt=system_prompt,
        user_prompt=_with_retry_guidance(
            prompt_builder(spec, node_input.blueprint, node_input.request),
            node_input.failure_messages,
        ),
        temperature=TEMP_RETRY,
        context_label=f"{node_input.section_key}_retry",
    )
    parsed_response = _parse_section_response(response_text, node_input.section_key)
    if node_input.section_key == "answer_key":
        return normalize_answer_key_payload(
            parsed_response,
            node_input.sections["check_in"],
            node_input.sections["assessment_passage"],
            node_input.sections["assessment_questions"],
        )
    return parsed_response


def _build_retry_node(section_key: str, attempt: int) -> Any:
    node_name = f"retry_{section_key}_{attempt}"

    @node(name=node_name)
    async def retry_node(node_input: RetryNodeInput) -> Any:
        return await _generate_retry_payload(node_input)

    return retry_node


async def _generate_intro_node(node_input: SectionNodeInput) -> dict[str, Any]:
    return await generate_intro(node_input.request, node_input.blueprint)


async def _generate_learning_targets_node(
    node_input: SectionNodeInput,
) -> dict[str, Any]:
    return await generate_learning_targets(node_input.request, node_input.blueprint)


async def _generate_warmup_node(node_input: SectionNodeInput) -> dict[str, Any]:
    return await generate_warmup(node_input.request, node_input.blueprint)


async def _generate_vocabulary_node(node_input: SectionNodeInput) -> dict[str, Any]:
    return await generate_vocabulary(node_input.request, node_input.blueprint)


async def _generate_key_points_node(node_input: SectionNodeInput) -> dict[str, Any]:
    return await generate_key_points(node_input.request, node_input.blueprint)


async def _generate_self_assessment_node(
    node_input: SectionNodeInput,
) -> dict[str, Any]:
    return await generate_self_assessment(node_input.request, node_input.blueprint)


async def _generate_core_explainer_node(
    node_input: SectionNodeInput,
) -> dict[str, Any]:
    return await generate_core_explainer(node_input.request, node_input.blueprint)


async def _generate_subconcept_node(
    node_input: SubconceptNodeInput,
) -> dict[str, Any]:
    return await generate_subconcept(
        node_input.request,
        node_input.blueprint,
        node_input.sub_competency,
    )


async def _generate_strategy_list_node(
    node_input: SectionNodeInput,
) -> dict[str, Any]:
    return await generate_strategy_list(node_input.request, node_input.blueprint)


async def _generate_deep_dive_node(node_input: SectionNodeInput) -> dict[str, Any]:
    return await generate_deep_dive(node_input.request, node_input.blueprint)


async def _generate_model_passage_node(
    node_input: SectionNodeInput,
) -> dict[str, Any]:
    return await generate_model_passage(node_input.request, node_input.blueprint)


async def _generate_assessment_passage_node(
    node_input: SectionNodeInput,
) -> dict[str, Any]:
    return await generate_assessment_passage(node_input.request, node_input.blueprint)


async def _generate_check_in_node(node_input: CheckInNodeInput) -> dict[str, Any]:
    return await generate_check_in(
        node_input.request,
        node_input.blueprint,
        node_input.model_passage,
    )


async def _generate_assessment_questions_node(
    node_input: AssessmentQuestionsNodeInput,
) -> dict[str, Any]:
    return await generate_assessment_questions(
        node_input.request,
        node_input.blueprint,
        node_input.assessment_passage,
    )


async def _generate_step_up_node(node_input: StepUpNodeInput) -> dict[str, Any]:
    return await generate_step_up(
        node_input.request,
        node_input.blueprint,
        node_input.assessment_passage,
        node_input.assessment_questions,
    )


async def _generate_answer_key_node(
    node_input: AnswerKeyNodeInput,
) -> dict[str, Any]:
    return await generate_answer_key(
        node_input.request,
        node_input.blueprint,
        node_input.model_passage,
        node_input.check_in,
        node_input.assessment_passage,
        node_input.assessment_questions,
        node_input.step_up,
    )


async def _generate_validation_node(
    node_input: ValidationNodeInput,
) -> ValidationResult:
    return await generate_validation(
        node_input.request,
        node_input.blueprint,
        node_input.sections,
    )


async def _generate_render_node(node_input: RenderNodeInput) -> GenerateResponse:
    return await generate_rendered_response(
        node_input.blueprint,
        node_input.sections,
        node_input.validation,
    )


intro_workflow_node = cast(
    Callable[[SectionNodeInput], Any], node(_generate_intro_node)
)
learning_targets_workflow_node = cast(
    Callable[[SectionNodeInput], Any],
    node(_generate_learning_targets_node),
)
warmup_workflow_node = cast(
    Callable[[SectionNodeInput], Any], node(_generate_warmup_node)
)
vocabulary_workflow_node = cast(
    Callable[[SectionNodeInput], Any],
    node(_generate_vocabulary_node),
)
key_points_workflow_node = cast(
    Callable[[SectionNodeInput], Any],
    node(_generate_key_points_node),
)
self_assessment_workflow_node = cast(
    Callable[[SectionNodeInput], Any],
    node(_generate_self_assessment_node),
)
core_explainer_workflow_node = cast(
    Callable[[SectionNodeInput], Any],
    node(_generate_core_explainer_node),
)
subconcept_workflow_node = cast(
    Callable[[SubconceptNodeInput], Any],
    node(_generate_subconcept_node),
)
strategy_list_workflow_node = cast(
    Callable[[SectionNodeInput], Any],
    node(_generate_strategy_list_node),
)
deep_dive_workflow_node = cast(
    Callable[[SectionNodeInput], Any],
    node(_generate_deep_dive_node),
)
model_passage_workflow_node = cast(
    Callable[[SectionNodeInput], Any],
    node(_generate_model_passage_node),
)
assessment_passage_workflow_node = cast(
    Callable[[SectionNodeInput], Any],
    node(_generate_assessment_passage_node),
)
check_in_workflow_node = cast(
    Callable[[CheckInNodeInput], Any],
    node(_generate_check_in_node),
)
assessment_questions_workflow_node = cast(
    Callable[[AssessmentQuestionsNodeInput], Any],
    node(_generate_assessment_questions_node),
)
step_up_workflow_node = cast(
    Callable[[StepUpNodeInput], Any],
    node(_generate_step_up_node),
)
answer_key_workflow_node = cast(
    Callable[[AnswerKeyNodeInput], Any],
    node(_generate_answer_key_node),
)
validation_workflow_node = cast(
    Callable[[ValidationNodeInput], Any],
    node(_generate_validation_node),
)
render_workflow_node = cast(
    Callable[[RenderNodeInput], Any],
    node(_generate_render_node),
)


@node(rerun_on_resume=True)
async def study_guide_workflow(
    ctx: Context,
    request: GenerateRequest,
) -> GenerateResponse:
    blueprint = await ctx.run_node(blueprint_node, request)
    shared_input = SectionNodeInput(request=request, blueprint=blueprint)

    wave1_results = await asyncio.gather(
        ctx.run_node(intro_workflow_node, shared_input),
        ctx.run_node(learning_targets_workflow_node, shared_input),
        ctx.run_node(warmup_workflow_node, shared_input),
        ctx.run_node(vocabulary_workflow_node, shared_input),
        ctx.run_node(key_points_workflow_node, shared_input),
        ctx.run_node(self_assessment_workflow_node, shared_input),
    )

    subconcept_inputs = [
        SubconceptNodeInput(
            request=request,
            blueprint=blueprint,
            sub_competency=sub_competency,
        )
        for sub_competency in blueprint.sub_competencies
    ]
    wave2_results = await asyncio.gather(
        ctx.run_node(core_explainer_workflow_node, shared_input),
        *[
            ctx.run_node(subconcept_workflow_node, subconcept_input)
            for subconcept_input in subconcept_inputs
        ],
        ctx.run_node(strategy_list_workflow_node, shared_input),
        ctx.run_node(deep_dive_workflow_node, shared_input),
        ctx.run_node(model_passage_workflow_node, shared_input),
        ctx.run_node(assessment_passage_workflow_node, shared_input),
    )

    (
        intro,
        learning_targets,
        warmup,
        vocabulary,
        key_points,
        self_assessment,
    ) = wave1_results

    core_explainer = wave2_results[0]
    subconcept_count = len(subconcept_inputs)
    subconcept = list(wave2_results[1 : 1 + subconcept_count])
    strategy_list = wave2_results[1 + subconcept_count]
    deep_dive = wave2_results[2 + subconcept_count]
    model_passage = wave2_results[3 + subconcept_count]
    assessment_passage = wave2_results[4 + subconcept_count]

    check_in, assessment_questions = await asyncio.gather(
        ctx.run_node(
            check_in_workflow_node,
            CheckInNodeInput(
                request=request,
                blueprint=blueprint,
                model_passage=model_passage,
            ),
        ),
        ctx.run_node(
            assessment_questions_workflow_node,
            AssessmentQuestionsNodeInput(
                request=request,
                blueprint=blueprint,
                assessment_passage=assessment_passage,
            ),
        ),
    )
    step_up = await ctx.run_node(
        step_up_workflow_node,
        StepUpNodeInput(
            request=request,
            blueprint=blueprint,
            assessment_passage=assessment_passage,
            assessment_questions=assessment_questions,
        ),
    )
    answer_key = await ctx.run_node(
        answer_key_workflow_node,
        AnswerKeyNodeInput(
            request=request,
            blueprint=blueprint,
            model_passage=model_passage,
            check_in=check_in,
            assessment_passage=assessment_passage,
            assessment_questions=assessment_questions,
            step_up=step_up,
        ),
    )

    sections: dict[str, Any] = {
        "intro": intro,
        "learning_targets": learning_targets,
        "warmup": warmup,
        "vocabulary": vocabulary,
        "core_explainer": core_explainer,
        "subconcept": subconcept,
        "strategy_list": strategy_list,
        "deep_dive": deep_dive,
        "model_passage": model_passage,
        "check_in": check_in,
        "key_points": key_points,
        "assessment_passage": assessment_passage,
        "assessment_questions": assessment_questions,
        "step_up": step_up,
        "self_assessment": self_assessment,
        "answer_key": answer_key,
    }
    sections["answer_key"] = normalize_answer_key_payload(
        sections["answer_key"],
        sections["check_in"],
        assessment_passage,
        assessment_questions,
    )

    validation = await ctx.run_node(
        validation_workflow_node,
        ValidationNodeInput(
            request=request,
            blueprint=blueprint,
            sections=sections,
        ),
    )

    retry_count = 0
    while not validation.passed and retry_count < 1:
        for section_key in validation.failed_sections:
            retry_node = _build_retry_node(section_key, retry_count + 1)
            sections[section_key] = await ctx.run_node(
                retry_node,
                RetryNodeInput(
                    request=request,
                    blueprint=blueprint,
                    sections=sections,
                    section_key=section_key,
                    failure_messages=validation.failures.get(section_key, []),
                ),
            )
            if section_key == "answer_key":
                sections[section_key] = normalize_answer_key_payload(
                    sections[section_key],
                    sections["check_in"],
                    sections["assessment_passage"],
                    sections["assessment_questions"],
                )
        validation = await ctx.run_node(
            validation_workflow_node,
            ValidationNodeInput(
                request=request,
                blueprint=blueprint,
                sections=sections,
            ),
        )
        retry_count += 1

    if not validation.passed:
        validation = validation.model_copy(
            update={
                "best_effort_sections": list(
                    dict.fromkeys(
                        [
                            *validation.best_effort_sections,
                            *validation.failed_sections,
                        ]
                    )
                )
            }
        )

    return await ctx.run_node(
        render_workflow_node,
        RenderNodeInput(
            blueprint=blueprint,
            sections=sections,
            validation=validation,
        ),
    )


root_agent = Workflow(
    name="study_guide_generator",
    description="Generates structured K-12 study guides from teacher-provided lesson inputs.",
    input_schema=GenerateRequest,
    output_schema=GenerateResponse,
    edges=[("START", study_guide_workflow)],
)

app = App(root_agent=root_agent, name="study_guide_agent")
