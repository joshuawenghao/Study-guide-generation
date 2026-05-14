from __future__ import annotations

from typing import Any

from app.types import Blueprint, GenerateRequest


def build_prompt(
    spec: dict[str, Any], blueprint: Blueprint, request: GenerateRequest
) -> str:
    assessment_passage = spec.get("assessment_passage", {})
    assessment_questions = spec.get("assessment_questions", {})

    passage_text = "\n".join(assessment_passage.get("passage", []))
    question_lines = "\n".join(
        f"- Q{item.get('number', '?')}: {item.get('question', '')}"
        for item in assessment_questions.get("questions", [])
    )

    step_up_schema = """{
    "title": "Step Up",
    "challenge_prompt": "string",
    "required_evidence": [
        "string"
    ],
    "success_criteria": [
        "string"
    ]
}"""

    prompt_lines = [
        "Create the step-up section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        f"- Assessment passage title: {assessment_passage.get('title', 'Assessment Passage')}",
        "- Assessment passage text:",
        passage_text,
        "- Upstream assessment questions:",
        question_lines or "- none provided",
        "Requirements:",
        "- Write one higher-order challenge_prompt that builds on the assessment questions.",
        "- Make the prompt require evidence from the assessment passage rather than opinion alone.",
        "- Include required_evidence and success_criteria lists that make expectations explicit.",
        f"- Keep the reading demand close to Grade {request.lesson_metadata.grade_level}.",
        "Expected JSON schema:",
        step_up_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
