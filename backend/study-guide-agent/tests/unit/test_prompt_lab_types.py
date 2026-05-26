from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.types import PromptLabGenerateRequest, PromptLabSectionKey


def _load_request_payload() -> dict[str, object]:
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "legacy_evals"
        / "english_grade6_ph.json"
    )
    fixture_payload = json.loads(fixture_path.read_text())
    fixture_input = fixture_payload["input"]
    fixture_input.setdefault("optional", {})
    return fixture_input


def test_prompt_lab_generate_request_accepts_supported_override_keys() -> None:
    payload = {
        "base_request": _load_request_payload(),
        "sample_case_id": "english_grade6_ph",
        "reviewer_label": "baseline-review",
        "prompt_overrides": {
            "system_prompt_append": "Prefer concise classroom language.",
            "section_overrides": {
                "intro": "Add one sentence that foregrounds the essential question.",
                "model_passage": "Keep the passage grounded in an everyday school context.",
            },
        },
    }

    request = PromptLabGenerateRequest.model_validate(payload)

    assert request.sample_case_id == "english_grade6_ph"
    assert request.reviewer_label == "baseline-review"
    assert request.prompt_overrides.system_prompt_append is not None
    assert request.prompt_overrides.section_overrides == {
        PromptLabSectionKey.INTRO: (
            "Add one sentence that foregrounds the essential question."
        ),
        PromptLabSectionKey.MODEL_PASSAGE: (
            "Keep the passage grounded in an everyday school context."
        ),
    }


def test_prompt_lab_generate_request_rejects_unsupported_override_keys() -> None:
    payload = {
        "base_request": _load_request_payload(),
        "prompt_overrides": {
            "section_overrides": {
                "blueprint": "Do not allow prompt-lab overrides for blueprint generation.",
            }
        },
    }

    with pytest.raises(ValidationError):
        PromptLabGenerateRequest.model_validate(payload)


def test_prompt_lab_generate_request_rejects_unknown_sample_case_id() -> None:
    payload = {
        "base_request": _load_request_payload(),
        "sample_case_id": "nursing_grade12_ph",
    }

    with pytest.raises(ValidationError):
        PromptLabGenerateRequest.model_validate(payload)
