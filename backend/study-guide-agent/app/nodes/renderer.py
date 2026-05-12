"""Renderer node for producing PDF and web preview study-guide artifacts."""

# ruff: noqa: E402

from __future__ import annotations

import base64
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.workflow import node

from app.types import (
    Blueprint,
    GenerateResponse,
    PreviewSection,
    ValidationResult,
    WebPreviewPayload,
)

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
TEMPLATE_NAME = "study_guide.html.j2"

CANONICAL_PREVIEW_ORDER: tuple[tuple[str, str], ...] = (
    ("intro", "intro"),
    ("learning_targets", "learning_targets"),
    ("warmup", "warmup"),
    ("vocabulary", "vocabulary"),
    ("core_explainer", "core_explainer"),
    ("subconcept", "subconcept"),
    ("strategy_list", "strategy_list"),
    ("deep_dive", "deep_dive"),
    ("model_passage", "model_passage"),
    ("check_in", "check_in"),
    ("key_points", "key_points"),
    ("assessment_passage", "assessment_passage"),
    ("assessment_questions", "assessment_questions"),
    ("step_up", "step_up"),
    ("self_assessment", "self_assessment"),
    ("answer_key", "answer_key"),
)


def _to_jsonable(payload: Any) -> Any:
    if isinstance(payload, BaseModel):
        return payload.model_dump(mode="json")
    if isinstance(payload, Mapping):
        return {str(key): _to_jsonable(value) for key, value in payload.items()}
    if isinstance(payload, Sequence) and not isinstance(
        payload, (str, bytes, bytearray)
    ):
        return [_to_jsonable(item) for item in payload]
    return payload


def _load_template() -> Any:
    from jinja2 import (
        Environment,
        FileSystemLoader,
        StrictUndefined,
        select_autoescape,
    )

    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml", "j2")),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return environment.get_template(TEMPLATE_NAME)


def _render_pdf_bytes(html: str) -> bytes:
    from weasyprint import HTML

    pdf_bytes = HTML(string=html).write_pdf()
    if pdf_bytes is None:
        raise RuntimeError("WeasyPrint returned no PDF bytes.")
    return pdf_bytes


def _render_html(
    *,
    blueprint: Blueprint,
    sections: Mapping[str, Any],
    validation: ValidationResult,
) -> str:
    template = _load_template()
    return cast(
        str,
        template.render(
            blueprint=_to_jsonable(blueprint),
            sections=_to_jsonable(sections),
            validation=_to_jsonable(validation),
        ),
    )


def _preview_title(section_key: str, payload: Any) -> str:
    if isinstance(payload, BaseModel):
        title = getattr(payload, "title", None)
        if isinstance(title, str) and title:
            return title
    if isinstance(payload, Mapping):
        title = payload.get("title")
        if isinstance(title, str) and title:
            return title
    return section_key.replace("_", " ").title()


def _iter_preview_entries(sections: Mapping[str, Any]) -> list[PreviewSection]:
    preview_sections: list[PreviewSection] = []

    for section_key, section_type in CANONICAL_PREVIEW_ORDER:
        payload = sections.get(section_key)
        if payload is None:
            continue

        if isinstance(payload, Sequence) and not isinstance(
            payload, (str, bytes, bytearray)
        ):
            for index, item in enumerate(payload, start=1):
                preview_sections.append(
                    PreviewSection(
                        section_id=f"{section_key}-{index}",
                        section_type=section_type,
                        title=_preview_title(section_key, item),
                        content=cast(dict[str, Any], _to_jsonable(item)),
                    )
                )
            continue

        preview_sections.append(
            PreviewSection(
                section_id=section_key,
                section_type=section_type,
                title=_preview_title(section_key, payload),
                content=cast(dict[str, Any], _to_jsonable(payload)),
            )
        )

    return preview_sections


async def generate_rendered_response(
    blueprint: Blueprint,
    sections: Mapping[str, Any],
    validation: ValidationResult,
) -> GenerateResponse:
    html = _render_html(
        blueprint=blueprint,
        sections=sections,
        validation=validation,
    )
    pdf_bytes = _render_pdf_bytes(html)
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    preview = WebPreviewPayload(sections=_iter_preview_entries(sections))

    return GenerateResponse(
        success=True,
        pdf_base64=pdf_base64,
        preview=preview,
        validation=validation,
        error=None,
    )


renderer_node = cast(
    Callable[[Blueprint, Mapping[str, Any], ValidationResult], Any],
    node(generate_rendered_response),
)
