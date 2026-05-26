from __future__ import annotations

from fastapi.testclient import TestClient

import app.fast_api_app as fast_api_module
from app.prompt_lab.samples import get_prompt_lab_sample, list_prompt_lab_samples


def test_list_prompt_lab_samples_returns_curated_cases_in_stable_order() -> None:
    samples = list_prompt_lab_samples()

    assert [sample.id for sample in samples] == [
        "english_grade6_ph",
        "math_grade4_vn",
    ]
    assert samples[0].request.lesson_metadata.subject == "English"
    assert samples[1].request.lesson_metadata.subject == "Mathematics"


def test_get_prompt_lab_sample_resolves_by_id() -> None:
    sample = get_prompt_lab_sample("english_grade6_ph")

    assert sample.label == "English Grade 6 PH"
    assert sample.request.lesson_metadata.lesson_code == "E6_Q1_0201"


def test_prompt_lab_samples_routes_return_catalog_and_item() -> None:
    with TestClient(fast_api_module.app) as client:
        catalog_response = client.get("/prompt-lab/samples")
        item_response = client.get("/prompt-lab/samples/math_grade4_vn")

    assert catalog_response.status_code == 200
    catalog_payload = catalog_response.json()
    assert [sample["id"] for sample in catalog_payload] == [
        "english_grade6_ph",
        "math_grade4_vn",
    ]

    assert item_response.status_code == 200
    item_payload = item_response.json()
    assert item_payload["id"] == "math_grade4_vn"
    assert item_payload["request"]["lesson_metadata"]["lesson_title"] == (
        "Comparing Fractions with Unlike Denominators"
    )
