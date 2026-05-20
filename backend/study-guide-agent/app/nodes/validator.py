"""Validator node for aggregating hard and soft study-guide validation results."""

# ruff: noqa: E402

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.nodes.sections.answer_key import normalize_answer_key_payload
from app.types import (
    AnswerKeySection,
    AssessmentPassageSection,
    AssessmentQuestionsSection,
    Blueprint,
    GenerateRequest,
    SelfAssessmentSection,
    ValidationResult,
)
from app.validators.hard.answer_key_quotes import validate_answer_key_quotes
from app.validators.hard.assessment_question_grounding import (
    validate_assessment_question_grounding,
)
from app.validators.hard.json_schema import validate_json_schema
from app.validators.hard.passage_domain_diff import validate_passage_domain_diff
from app.validators.hard.self_assess_targets import validate_self_assess_targets
from app.validators.hard.vocab_presence import validate_vocab_presence
from app.validators.soft.answer_leakage import validate_answer_leakage
from app.validators.soft.reading_level import validate_reading_level


def _empty_result() -> ValidationResult:
    return ValidationResult(
        passed=True,
        failed_sections=[],
        failures={},
        warnings=[],
        best_effort_sections=[],
    )


def _merge_results(
    base: ValidationResult, incoming: ValidationResult
) -> ValidationResult:
    failed_sections = list(base.failed_sections)
    for section_key in incoming.failed_sections:
        if section_key not in failed_sections:
            failed_sections.append(section_key)

    failures = {
        section_key: list(messages) for section_key, messages in base.failures.items()
    }
    for section_key, messages in incoming.failures.items():
        failures.setdefault(section_key, []).extend(messages)

    best_effort_sections = list(base.best_effort_sections)
    for section_key in incoming.best_effort_sections:
        if section_key not in best_effort_sections:
            best_effort_sections.append(section_key)

    return ValidationResult(
        passed=base.passed and incoming.passed,
        failed_sections=failed_sections,
        failures=failures,
        warnings=[*base.warnings, *incoming.warnings],
        best_effort_sections=best_effort_sections,
    )


def _missing_section_result(section_key: str) -> ValidationResult:
    return ValidationResult(
        passed=False,
        failed_sections=[section_key],
        failures={
            section_key: [
                f"Required section '{section_key}' is missing for validation."
            ]
        },
        warnings=[],
        best_effort_sections=[],
    )


def _iter_schema_payloads(payload: Any) -> Sequence[Any]:
    if isinstance(payload, Sequence) and not isinstance(
        payload, (str, bytes, bytearray)
    ):
        return payload or [payload]
    return [payload]


async def generate_validation(
    request: GenerateRequest,
    blueprint: Blueprint,
    sections: Mapping[str, Any],
) -> ValidationResult:
    result = _empty_result()
    schema_failed_sections: set[str] = set()

    for section_key, payload in sections.items():
        for schema_payload in _iter_schema_payloads(payload):
            schema_result = validate_json_schema(
                section_key=section_key,
                payload=schema_payload,
            )
            result = _merge_results(result, schema_result)
            if not schema_result.passed:
                schema_failed_sections.add(section_key)

    result = _merge_results(result, validate_passage_domain_diff(blueprint=blueprint))
    result = _merge_results(
        result,
        validate_vocab_presence(blueprint=blueprint, section_payloads=sections),
    )

    self_assessment_payload = sections.get("self_assessment")
    if self_assessment_payload is None:
        result = _merge_results(result, _missing_section_result("self_assessment"))
    elif "self_assessment" not in schema_failed_sections:
        result = _merge_results(
            result,
            validate_self_assess_targets(
                blueprint=blueprint,
                self_assessment=SelfAssessmentSection.model_validate(
                    self_assessment_payload
                ),
            ),
        )

    answer_key_payload = sections.get("answer_key")
    assessment_passage_payload = sections.get("assessment_passage")
    assessment_questions_payload = sections.get("assessment_questions")
    if answer_key_payload is None:
        result = _merge_results(result, _missing_section_result("answer_key"))
    if assessment_passage_payload is None:
        result = _merge_results(result, _missing_section_result("assessment_passage"))

    validated_answer_key: AnswerKeySection | None = None
    validated_assessment_passage: AssessmentPassageSection | None = None
    validated_assessment_questions: AssessmentQuestionsSection | None = None
    if (
        assessment_passage_payload is not None
        and "assessment_passage" not in schema_failed_sections
    ):
        validated_assessment_passage = AssessmentPassageSection.model_validate(
            assessment_passage_payload
        )
    if (
        assessment_questions_payload is not None
        and "assessment_questions" not in schema_failed_sections
    ):
        validated_assessment_questions = AssessmentQuestionsSection.model_validate(
            assessment_questions_payload
        )

    normalized_answer_key_payload = answer_key_payload
    if (
        answer_key_payload is not None
        and validated_assessment_passage is not None
        and validated_assessment_questions is not None
    ):
        normalized_answer_key_payload = normalize_answer_key_payload(
            dict(answer_key_payload),
            validated_assessment_passage.model_dump(mode="json"),
            validated_assessment_questions.model_dump(mode="json"),
        )

    if (
        normalized_answer_key_payload is not None
        and "answer_key" not in schema_failed_sections
    ):
        validated_answer_key = AnswerKeySection.model_validate(
            normalized_answer_key_payload
        )

    if (
        validated_assessment_questions is not None
        and validated_assessment_passage is not None
    ):
        result = _merge_results(
            result,
            validate_assessment_question_grounding(
                assessment_questions=validated_assessment_questions,
                assessment_passage=validated_assessment_passage,
            ),
        )

    if validated_answer_key is not None and validated_assessment_passage is not None:
        result = _merge_results(
            result,
            validate_answer_key_quotes(
                answer_key=validated_answer_key,
                assessment_passage=validated_assessment_passage,
            ),
        )
        result = _merge_results(
            result,
            validate_answer_leakage(
                answer_key=validated_answer_key,
                section_payloads=sections,
            ),
        )

    result = _merge_results(
        result,
        validate_reading_level(
            target_grade_level=request.lesson_metadata.grade_level,
            section_payloads=sections,
        ),
    )

    return result


validator_node = cast(
    Callable[[GenerateRequest, Blueprint, Mapping[str, Any]], Any],
    node(generate_validation),
)
