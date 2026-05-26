"""Curated prompt-lab sample inputs for reviewer-facing experiments."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from app.types import (
    PROMPT_LAB_SAMPLE_CASE_IDS,
    PromptLabSampleCaseId,
    PromptLabSampleInput,
)

SAMPLE_INPUTS_DIR = Path(__file__).resolve().parent / "sample_inputs"

_SAMPLE_FILE_NAMES: dict[PromptLabSampleCaseId, str] = {
    PromptLabSampleCaseId.ENGLISH_GRADE6_PH: "english_grade6_ph.json",
    PromptLabSampleCaseId.MATH_GRADE4_VN: "math_grade4_vn.json",
}


@cache
def _load_prompt_lab_sample(
    sample_id: PromptLabSampleCaseId,
) -> PromptLabSampleInput:
    sample_path = SAMPLE_INPUTS_DIR / _SAMPLE_FILE_NAMES[sample_id]
    payload = json.loads(sample_path.read_text())
    return PromptLabSampleInput.model_validate(payload)


def list_prompt_lab_samples() -> list[PromptLabSampleInput]:
    return [
        _load_prompt_lab_sample(sample_id)
        for sample_id in PROMPT_LAB_SAMPLE_CASE_IDS
        if sample_id in _SAMPLE_FILE_NAMES
    ]


def get_prompt_lab_sample(sample_id: str) -> PromptLabSampleInput:
    try:
        resolved_sample_id = PromptLabSampleCaseId(sample_id)
    except ValueError as exc:
        raise KeyError(sample_id) from exc

    if resolved_sample_id not in _SAMPLE_FILE_NAMES:
        raise KeyError(sample_id)

    return _load_prompt_lab_sample(resolved_sample_id)
