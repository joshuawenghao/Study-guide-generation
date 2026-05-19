from __future__ import annotations

from typing import Any

from app.types import Blueprint, GenerateRequest


def _build_quote_bank(assessment_passage: dict[str, Any]) -> list[str]:
    passage_lines = [
        str(item).strip()
        for item in assessment_passage.get("passage", [])
        if str(item).strip()
    ]
    passage_text = "\n".join(passage_lines)

    quote_bank: list[str] = []
    for clue in assessment_passage.get("evidence_clues", []):
        normalized_clue = str(clue).strip()
        if (
            normalized_clue
            and normalized_clue in passage_text
            and normalized_clue not in quote_bank
        ):
            quote_bank.append(normalized_clue)

    for paragraph in passage_lines:
        sentence = paragraph.strip()
        if sentence and sentence not in quote_bank:
            quote_bank.append(sentence)

        for fragment in sentence.replace(";", ",").split(","):
            normalized_fragment = fragment.strip()
            if (
                len(normalized_fragment.split()) >= 3
                and normalized_fragment in passage_text
                and normalized_fragment not in quote_bank
            ):
                quote_bank.append(normalized_fragment)

    return quote_bank[:8]


def build_prompt(
    spec: dict[str, Any], blueprint: Blueprint, request: GenerateRequest
) -> str:
    del request

    check_in = spec.get("check_in", {})
    assessment_passage = spec.get("assessment_passage", {})
    assessment_questions = spec.get("assessment_questions", {})
    step_up = spec.get("step_up", {})

    check_in_questions = "\n".join(
        f"- Q{item.get('number', '?')}: {item.get('question', '')}"
        for item in check_in.get("questions", [])
    )
    assessment_passage_text = "\n".join(assessment_passage.get("passage", []))
    assessment_questions_text = "\n".join(
        f"- Q{item.get('number', '?')}: {item.get('question', '')}"
        for item in assessment_questions.get("questions", [])
    )
    quote_bank = _build_quote_bank(assessment_passage)
    quote_bank_text = "\n".join(f'- "{quote}"' for quote in quote_bank)
    step_up_prompt = step_up.get("challenge_prompt", "")
    step_up_evidence = "\n".join(
        f"- {item}" for item in step_up.get("required_evidence", [])
    )

    answer_key_schema = """{
    "title": "Answer Key",
    "check_in_answers": [
        {
            "question_number": 1,
            "question": "string",
            "possible_answer": "string",
            "evidence_quote": "string"
        }
    ],
    "assessment_answers": [
        {
            "question_number": 1,
            "question": "string",
            "possible_answer": "string",
            "evidence_quote": "string"
        }
    ],
    "step_up_answer": {
        "challenge_response": "string",
        "required_evidence": [
            "string"
        ]
    },
    "teacher_note": "string"
}"""

    prompt_lines = [
        "Create the answer key section for a K-12 study guide.",
        f"- Lesson title: {blueprint.title}",
        f"- Essential question: {blueprint.essential_question}",
        "- Check-in questions:",
        check_in_questions or "- none provided",
        "- Assessment passage text:",
        assessment_passage_text,
        "- Exact quote bank for assessment answers (use only these exact strings when you quote evidence):",
        quote_bank_text or "- none provided",
        "- Assessment questions:",
        assessment_questions_text or "- none provided",
        "- Step-up prompt:",
        step_up_prompt or "- none provided",
        "- Step-up required evidence:",
        step_up_evidence or "- none provided",
        "Requirements:",
        "- Provide one answer-key entry per check-in question and per assessment question.",
        "- Every possible_answer for assessment questions must contain at least one verbatim quoted phrase from the assessment passage.",
        '- For each assessment answer, write the quote directly inside possible_answer, for example: The passage informs readers because "hand hygiene prevents infection" states the core idea.',
        "- Include an evidence_quote field that repeats the exact quoted phrase used from the assessment passage.",
        "- For assessment answers, choose evidence only from the exact quote bank above. Do not invent, combine, shorten, or paraphrase quoted evidence.",
        "- Provide a step_up_answer object that answers the step-up prompt directly and repeats the required_evidence list.",
        "- Keep answers concise, student-appropriate, and structurally ready for downstream quote validation.",
        "Expected JSON schema:",
        answer_key_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
