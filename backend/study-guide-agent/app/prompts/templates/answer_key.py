from __future__ import annotations

import re
from typing import Any

from app.types import Blueprint, GenerateRequest


def _score_quote_for_question(
    candidate: str, question_text: str, evidence_hint: str
) -> float:
    """Score a passage fragment by relevance to a specific question.

    evidence_hint is weighted 3x because it was written to point at the right excerpt.
    """

    def _token_set(text: str) -> set[str]:
        return {t for t in re.findall(r"[A-Za-z0-9\']+", text.lower()) if t}

    def _overlap(a: str, b: str) -> float:
        a_tok, b_tok = _token_set(a), _token_set(b)
        if not a_tok or not b_tok:
            return 0.0
        return len(a_tok & b_tok) / len(a_tok | b_tok)

    hint_score = _overlap(candidate, evidence_hint) * 3.0 if evidence_hint else 0.0
    question_score = _overlap(candidate, question_text) * 1.5 if question_text else 0.0
    return hint_score + question_score


def _build_all_quote_candidates(assessment_passage: dict[str, Any]) -> list[str]:
    """Full candidate pool from a passage — no cap, evidence_clues listed first."""
    passage_lines = [
        str(item).strip()
        for item in assessment_passage.get("passage", [])
        if str(item).strip()
    ]
    passage_text = "\n".join(passage_lines)

    candidates: list[str] = []
    for clue in assessment_passage.get("evidence_clues", []):
        normalized_clue = str(clue).strip()
        if (
            normalized_clue
            and normalized_clue in passage_text
            and normalized_clue not in candidates
        ):
            candidates.append(normalized_clue)

    for paragraph in passage_lines:
        sentence = paragraph.strip()
        if sentence and sentence not in candidates:
            candidates.append(sentence)
        for fragment in sentence.replace(";", ",").split(","):
            normalized_fragment = fragment.strip()
            if (
                len(normalized_fragment.split()) >= 3
                and normalized_fragment in passage_text
                and normalized_fragment not in candidates
            ):
                candidates.append(normalized_fragment)

    return candidates


def _top_quotes_for_question(
    assessment_passage: dict[str, Any],
    question_text: str,
    evidence_hint: str,
    n: int = 3,
) -> list[str]:
    """Return up to n passage fragments most relevant to this question."""
    candidates = _build_all_quote_candidates(assessment_passage)
    if not candidates:
        return []
    return sorted(
        candidates,
        key=lambda c: _score_quote_for_question(c, question_text, evidence_hint),
        reverse=True,
    )[:n]


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
    _aq_blocks: list[str] = []
    for _item in assessment_questions.get("questions", []):
        _q_num = _item.get("number", "?")
        _q_text = str(_item.get("question", ""))
        _hint = str(_item.get("evidence_hint", ""))
        _resp = str(_item.get("expected_response_type", ""))
        _suggested = _top_quotes_for_question(assessment_passage, _q_text, _hint, n=3)
        _block_lines = [
            f"- Q{_q_num}: {_q_text}",
            f"  - Evidence hint: {_hint}",
            f"  - Expected response type: {_resp}",
        ]
        if _suggested:
            _block_lines.append(
                "  - Suggested verbatim quotes for evidence_quote (copy one exactly):"
            )
            for _q in _suggested:
                _block_lines.append(f'    * "{_q}"')
        _aq_blocks.append("\n".join(_block_lines))
    assessment_questions_text = "\n".join(_aq_blocks)
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
        "- Assessment questions (each with suggested verbatim quotes):",
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
        "- For each assessment_answers entry, choose exactly one evidence_quote from the suggested quotes listed with that question and copy it verbatim.",
        "- Do not place raw double-quoted evidence inside free-text fields such as check-in answers, step_up_answer.challenge_response, or teacher_note.",
        "- Provide a step_up_answer object that answers the step-up prompt directly and repeats the required_evidence list.",
        "- Keep answers concise, student-appropriate, and structurally ready for downstream quote validation.",
        "Expected JSON schema:",
        answer_key_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)
