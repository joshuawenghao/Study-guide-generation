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
    model_passage = spec.get("model_passage", {})
    assessment_passage = spec.get("assessment_passage", {})
    assessment_questions = spec.get("assessment_questions", {})
    step_up = spec.get("step_up", {})

    check_in_questions = "\n".join(
        "\n".join(
            [
                f"Q{item.get('number', '?')}: {item.get('question', '')}",
                f"  - Evidence hint: {item.get('evidence_hint', '')}",
                f"  - Expected response type: {item.get('expected_response_type', '')}",
            ]
        )
        for item in check_in.get("questions", [])
    )
    model_passage_text = "\n".join(model_passage.get("passage", []))
    model_quote_bank = _build_quote_bank(model_passage)
    model_quote_bank_text = "\n".join(f'- "{quote}"' for quote in model_quote_bank)
    assessment_passage_text = "\n".join(assessment_passage.get("passage", []))
    assessment_questions_text = "\n".join(
        "\n".join(
            [
                f"- Q{item.get('number', '?')}: {item.get('question', '')}",
                f"  - Evidence hint: {item.get('evidence_hint', '')}",
                f"  - Expected response type: {item.get('expected_response_type', '')}",
            ]
        )
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
        "- Model passage text for check-in answers:",
        model_passage_text or "- none provided",
        "- Exact quote bank for check-in answers (choose exactly one per question):",
        model_quote_bank_text or "- none provided",
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
        "- Provide one answer-key entry per check-in question.",
        "- For check_in_answers, use the model passage text above as the sole source of truth.",
        "- For each check_in_answers entry, choose exactly one evidence_quote from the check-in quote bank above and copy it verbatim.",
        "- Use the evidence hint to choose the most specific supporting quote before writing possible_answer.",
        "- Do not reuse a generic check-in evidence_quote for multiple different questions when a more specific quote is available.",
        "- Keep check_in_answers in the exact same order as the check-in questions above.",
        "- Copy each check_in_answers.question_number and check_in_answers.question exactly from the check-in questions above.",
        "- Answer only the specific check-in question attached to that entry; never swap or reuse an answer for a different check-in question.",
        "- Provide one assessment_answers entry per assessment question.",
        "- Keep assessment_answers in the exact same order as the assessment questions above.",
        "- Copy each assessment_answers.question_number and assessment_answers.question exactly from the assessment questions above.",
        "- For each assessment_answers entry, write possible_answer as a concise model answer to the question itself.",
        "- Match the specificity of the check-in answers: answer the full assessment question directly instead of reducing it to a generic passage-summary sentence.",
        "- Use the assessment question's evidence_hint and expected_response_type to keep the answer aligned to the student-facing prompt.",
        "- Do not write generic meta-instructions such as 'The correct answer should...' or 'Respond directly to the question.' Write the actual answer instead.",
        "- Keep the exact quoted evidence only in evidence_quote. Do not repeat the exact evidence_quote inside possible_answer.",
        "- For each assessment_answers entry, choose exactly one evidence_quote from the assessment quote bank above and copy it verbatim.",
        "- Do not place raw double-quoted evidence inside free-text fields such as check-in answers, step_up_answer.challenge_response, or teacher_note.",
        "- Provide a step_up_answer object that answers the step-up prompt directly and repeats the required_evidence list.",
        "- Keep answers concise, student-appropriate, and structurally ready for downstream quote validation.",
        "Expected JSON schema:",
        answer_key_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
