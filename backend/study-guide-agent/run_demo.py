from __future__ import annotations

import argparse
import asyncio
import base64
import json
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from app.agent import study_guide_workflow
from app.nodes.renderer import generate_rendered_response
from app.types import (
    Blueprint,
    GenerateRequest,
    LearningTarget,
    SubCompetency,
    TopicDomains,
    ValidationResult,
    VocabEntry,
)

DEFAULT_FIXTURE_PATH = Path("tests/fixtures/legacy_evals/english_grade6_ph.json")
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "demo-output"


class FakeContext:
    async def run_node(self, node: Any, node_input: Any = None) -> Any:
        return await node._func(node_input)


def _normalize_request_payload(payload: dict[str, Any]) -> dict[str, Any]:
    request_payload = payload.get("input", payload)
    if not isinstance(request_payload, dict):
        raise ValueError("Demo input payload must be a JSON object.")
    request_payload.setdefault("optional", {})
    optional_value = request_payload["optional"]
    if not isinstance(optional_value, dict):
        raise ValueError("The optional field must be a JSON object when provided.")
    return request_payload


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, Mapping):
            merged[key] = _deep_merge(existing, value)
            continue
        merged[key] = value
    return merged


def _build_demo_blueprint() -> Blueprint:
    return Blueprint(
        lesson_id="ENG6-U1-L2",
        title="Author Purpose",
        essential_question="Why does author purpose matter?",
        introduction_hook="Texts can guide readers in different ways.",
        learning_targets=[
            LearningTarget(
                number=1,
                bloom_verb="identify",
                objective="Identify how authors signal purpose.",
            )
        ],
        vocabulary=[
            VocabEntry(
                word="audience",
                definition="The people a text is meant for.",
                example_sentence=(
                    "The writer considered the audience before choosing details."
                ),
            )
        ],
        topic_domains=TopicDomains(
            model_passage="school talent show announcement",
            assessment_passage="mangrove forest protection article",
        ),
        sub_competencies=[SubCompetency(id="sc-1", label="Purpose clues")],
        core_concept="Authors choose details for a purpose.",
        deep_dive_dimensions=["entertain", "inform", "persuade"],
    )


def _build_demo_validation() -> ValidationResult:
    return ValidationResult(
        passed=True,
        failed_sections=[],
        failures={},
        warnings=["Reading level slightly above target for intro."],
        best_effort_sections=[],
    )


def _build_demo_sections() -> dict[str, object]:
    return {
        "answer_key": {
            "title": "Answer Key",
            "check_in_answers": [],
            "assessment_answers": [],
            "step_up_answer": {
                "challenge_response": "Use passage evidence to explain the purpose.",
                "required_evidence": ["quoted phrase"],
            },
            "teacher_note": "Accept equivalent answers with evidence.",
        },
        "subconcept": [
            {
                "title": "Subconcept One",
                "sub_competency_id": "sc-1",
                "sub_competency_label": "Purpose clues",
                "explanation": "Clues in a text reveal purpose.",
                "worked_example": "A poster uses commands to persuade.",
                "quick_check": {
                    "question": "What clue shows persuasion?",
                    "expected_answer": "The command tells the reader what to do.",
                },
            }
        ],
        "intro": {
            "title": "Introduction",
            "hook": "Think about how authors choose details.",
            "essential_question": "Why does author purpose matter?",
            "paragraphs": ["Authors choose details to guide the reader clearly."],
            "bridge_to_lesson": "You will study those choices today.",
        },
    }


def _load_default_request_payload(fixture_path: Path) -> dict[str, Any]:
    fixture_payload = json.loads(fixture_path.read_text())
    if not isinstance(fixture_payload, dict):
        raise ValueError("Fixture file must contain a JSON object.")
    return _normalize_request_payload(fixture_payload)


def _load_request(
    fixture_path: Path,
    custom_input_path: Path | None = None,
) -> GenerateRequest:
    request_payload = _load_default_request_payload(fixture_path)
    if custom_input_path is not None:
        custom_payload = json.loads(custom_input_path.read_text())
        if not isinstance(custom_payload, dict):
            raise ValueError("Custom input file must contain a JSON object.")
        request_payload = _deep_merge(
            request_payload,
            _normalize_request_payload(custom_payload),
        )
    return GenerateRequest.model_validate(request_payload)


async def _run_workflow(request: GenerateRequest) -> Any:
    workflow_node = cast(Any, study_guide_workflow)
    return await workflow_node._func(FakeContext(), request)


async def _run_renderer_only(output_path: Path) -> dict[str, object]:
    response = await generate_rendered_response(
        blueprint=_build_demo_blueprint(),
        sections=_build_demo_sections(),
        validation=_build_demo_validation(),
    )
    pdf_bytes = base64.b64decode(response.pdf_base64)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)
    return {
        "mode": "renderer-only",
        "success": response.success,
        "output_path": str(output_path),
        "pdf_bytes": len(pdf_bytes),
        "preview_sections": len(response.preview.sections),
        "validation_warning_count": len(response.validation.warnings),
    }


async def _run_full_workflow(
    output_path: Path,
    fixture_path: Path,
    custom_input_path: Path | None,
) -> dict[str, object]:
    request = _load_request(fixture_path, custom_input_path)
    response = await _run_workflow(request)
    pdf_bytes = base64.b64decode(response.pdf_base64)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)
    return {
        "mode": "full-workflow",
        "success": response.success,
        "output_path": str(output_path),
        "pdf_bytes": len(pdf_bytes),
        "preview_sections": len(response.preview.sections),
        "validation_warning_count": len(response.validation.warnings),
        "request_lesson_code": request.lesson_metadata.lesson_code,
        "validation_warnings": response.validation.warnings,
    }


def _default_output_path(mode: str) -> Path:
    file_name = (
        "study-guide-demo.pdf"
        if mode == "renderer-only"
        else "study-guide-full-demo.pdf"
    )
    return DEFAULT_OUTPUT_DIR / file_name


def _open_output_file(output_path: Path) -> bool:
    if sys.platform == "darwin":
        opener = "open"
    elif sys.platform.startswith("linux") and shutil.which("xdg-open"):
        opener = "xdg-open"
    else:
        return False

    subprocess.run([opener, str(output_path)], check=False)
    return True


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a local study-guide demo PDF."
    )
    parser.add_argument(
        "--mode",
        choices=("renderer-only", "full-workflow"),
        default="renderer-only",
        help="Choose the renderer-only proof or the full workflow run.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Where to write the generated PDF.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE_PATH,
        help="Fixture used for the full workflow mode.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "Optional JSON file with teacher-style request values. It may contain "
            "either a full GenerateRequest object or a partial override merged onto "
            "the default fixture."
        ),
    )
    parser.add_argument(
        "--print-default-input",
        action="store_true",
        help="Print the default full-workflow request JSON and exit.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated PDF with the local desktop viewer after writing it.",
    )
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    if args.print_default_input:
        print(json.dumps(_load_default_request_payload(args.fixture), indent=2))
        return 0

    output_path = args.output
    if output_path is None:
        output_path = _default_output_path(args.mode)

    if args.mode == "renderer-only":
        summary = await _run_renderer_only(output_path)
    else:
        summary = await _run_full_workflow(output_path, args.fixture, args.input)

    if args.open:
        summary["opened"] = _open_output_file(output_path)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
