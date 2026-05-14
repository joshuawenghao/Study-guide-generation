from __future__ import annotations

from app.types import Blueprint, GenerateRequest, SubCompetency


def build_prompt(
    spec: SubCompetency, blueprint: Blueprint, request: GenerateRequest
) -> str:
    subconcept_schema = """{
    "title": "string",
    "sub_competency_id": "string",
    "sub_competency_label": "string",
    "explanation": "string",
    "worked_example": "string",
    "quick_check": {
        "question": "string",
        "expected_answer": "string"
    }
}"""

    prompt_lines = [
        "Create one sub-concept section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Core concept: {blueprint.core_concept}",
        f"- Target sub-competency id: {spec.id}",
        f"- Target sub-competency label: {spec.label}",
        "Requirements:",
        "- Focus only on the provided sub-competency.",
        "- Explain the sub-concept clearly in student-facing language.",
        "- Include one worked_example that directly illustrates the target sub-competency.",
        "- Include one quick_check with a short expected answer to confirm understanding.",
        f"- Keep the reading level close to Grade {request.lesson_metadata.grade_level}.",
        "- Use short sentences and concrete examples that a student can picture quickly.",
        "- Keep the explanation and worked_example direct rather than academic or abstract.",
        "Expected JSON schema:",
        subconcept_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
