from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.nodes.sections as sections_module
from app.nodes.base import MAX_OUTPUT_TOKENS, MAX_STRATEGY_LIST_OUTPUT_TOKENS
from app.nodes.sections import assessment_passage as assessment_passage_module
from app.nodes.sections import core_explainer as core_explainer_module
from app.nodes.sections import deep_dive as deep_dive_module
from app.nodes.sections import model_passage as model_passage_module
from app.nodes.sections import strategy_list as strategy_list_module
from app.nodes.sections import subconcept as subconcept_module
from app.types import Blueprint, GenerateRequest


def _load_request_from_fixture() -> GenerateRequest:
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "legacy_evals"
        / "english_grade6_ph.json"
    )
    fixture_payload = json.loads(fixture_path.read_text())
    fixture_input = fixture_payload["input"]
    fixture_input.setdefault("optional", {})
    return GenerateRequest.model_validate(fixture_input)


def _build_blueprint(request: GenerateRequest) -> Blueprint:
    return Blueprint.model_validate(
        {
            "lesson_id": request.lesson_metadata.lesson_code,
            "title": request.lesson_metadata.lesson_title,
            "essential_question": "Why does it matter why an author wrote something?",
            "introduction_hook": "Compare three texts about the same topic that each try to do something different.",
            "learning_targets": [
                {
                    "number": 1,
                    "bloom_verb": request.instructional_design.bloom_targets[0],
                    "objective": "I can identify the three main author purposes: entertain, inform, and persuade.",
                },
                {
                    "number": 2,
                    "bloom_verb": request.instructional_design.bloom_targets[1],
                    "objective": "I can explain how language and tone show an author's purpose.",
                },
                {
                    "number": 3,
                    "bloom_verb": request.instructional_design.bloom_targets[2],
                    "objective": "I can apply purpose identification to a new passage.",
                },
            ],
            "vocabulary": [
                {
                    "word": "author's purpose",
                    "definition": "The reason an author writes a text.",
                    "example_sentence": "We looked for the author's purpose before answering the questions.",
                },
                {
                    "word": "entertain",
                    "definition": "To make the reader enjoy the text.",
                    "example_sentence": "The funny story was written to entertain the reader.",
                },
                {
                    "word": "inform",
                    "definition": "To teach or give facts to the reader.",
                    "example_sentence": "The article was written to inform us about volcano safety.",
                },
                {
                    "word": "persuade",
                    "definition": "To convince the reader to think or do something.",
                    "example_sentence": "The poster tried to persuade students to recycle.",
                },
                {
                    "word": "tone",
                    "definition": "The feeling or attitude shown in writing.",
                    "example_sentence": "The serious tone helped show that the text was meant to inform.",
                },
            ],
            "topic_domains": {
                "model_passage": "school talent show announcement",
                "assessment_passage": "mangrove forest protection article",            },
            "sub_competencies": [
                item.model_dump() for item in request.curriculum.sub_competencies
            ],
            "core_concept": request.instructional_design.core_concept,
            "deep_dive_dimensions": ["entertain", "inform", "persuade"],
            }
    )


@pytest.mark.asyncio
async def test_wave2_section_nodes_generate_structured_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    first_subcompetency = blueprint.sub_competencies[0]

    async def fake_call_gemini(
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int = MAX_OUTPUT_TOKENS,
        max_retries: int = 2,
        context_label: str = "unknown",
    ) -> str:
        assert "PH Grade 6 English" in system_prompt
        assert request.lesson_metadata.lesson_title in user_prompt
        assert temperature == sections_module.TEMP_SECTION
        expected_output_tokens = (
            MAX_STRATEGY_LIST_OUTPUT_TOKENS
            if context_label == "strategy_list"
            else MAX_OUTPUT_TOKENS
        )
        assert max_output_tokens == expected_output_tokens
        assert max_retries == 2

        expected_fragments = {
            "core_explainer": [blueprint.core_concept, first_subcompetency.label],
            "subconcept": [first_subcompetency.id, first_subcompetency.label],
            "strategy_list": [blueprint.essential_question],
            "deep_dive": blueprint.deep_dive_dimensions,
            "model_passage": [blueprint.topic_domains.model_passage],
            "assessment_passage": [
                blueprint.topic_domains.assessment_passage,
                blueprint.topic_domains.model_passage,
            ],
        }
        for fragment in expected_fragments[context_label]:
            assert fragment in user_prompt

        return json.dumps(
            {
                "title": context_label.replace("_", " ").title(),
                "context_label": context_label,
                "items": [request.lesson_metadata.lesson_code],
            }
        )

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    modules = [
        (core_explainer_module.generate_core_explainer, "core_explainer", []),
        (
            subconcept_module.generate_subconcept,
            "subconcept",
            [first_subcompetency],
        ),
        (strategy_list_module.generate_strategy_list, "strategy_list", []),
        (deep_dive_module.generate_deep_dive, "deep_dive", []),
        (model_passage_module.generate_model_passage, "model_passage", []),
        (
            assessment_passage_module.generate_assessment_passage,
            "assessment_passage",
            [],
        ),
    ]

    for generator, expected_label, extra_args in modules:
        result = await generator(request, blueprint, *extra_args)

        assert result["context_label"] == expected_label
        assert result["items"] == [request.lesson_metadata.lesson_code]


@pytest.mark.asyncio
async def test_wave2_section_nodes_raise_on_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return "not-json"

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    with pytest.raises(
        RuntimeError, match="Failed to parse model_passage response as JSON"
    ):
        await model_passage_module.generate_model_passage(request, blueprint)


@pytest.mark.asyncio
async def test_wave2_section_nodes_repair_lone_backslashes_in_json_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        valid_payload = json.dumps(
            {
                "title": "Model Passage",
                "topic_domain": "fraction tiles",
                "genre": "explanation",
                "passage": ["Compare 1/2 and \\frac{3}{4} using a common denominator."],
                "text_features": ["comparison words"],
                "evidence_focus": "The comparison sentence.",
            }
        )
        return valid_payload.replace("\\\\frac", "\\frac")

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await model_passage_module.generate_model_passage(request, blueprint)

    assert result["passage"] == [
        "Compare 1/2 and \\frac{3}{4} using a common denominator."
    ]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_html_like_markup_from_payload_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Assessment Passage",
                "topic_domain": "infection prevention",
                "genre": "article",
                "passage": [
                    "<b>Hand hygiene</b> helps prevent infection.<br>It protects patients.",
                ],
                "evidence_clues": [
                    "&lt;b&gt;clean hands&lt;/b&gt; reduce contamination"
                ],
                "answerability_note": "Use <i>plain</i> evidence from the text.",
            }
        )

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "Hand hygiene helps prevent infection.\nIt protects patients."
    ]
    assert result["evidence_clues"] == ["clean hands reduce contamination"]
    assert result["answerability_note"] == "Use plain evidence from the text."


@pytest.mark.asyncio
async def test_wave2_section_nodes_decode_literal_display_escapes_in_payload_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)
    first_subcompetency = blueprint.sub_competencies[0]

    async def fake_call_gemini(**_: object) -> str:
        return json.dumps(
            {
                "title": "Subconcept",
                "sub_competency_id": first_subcompetency.id,
                "sub_competency_label": first_subcompetency.label,
                "explanation": "Read the problem\\nthen identify the clue.",
                "worked_example": "A poster says,\\nJoin the clean-up drive today!",
                "quick_check": {
                    "question": "What clue shows persuasion?",
                    "expected_answer": "The command word shows what to do.\\nIt guides the reader clearly.",
                },
            }
        )

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await subconcept_module.generate_subconcept(
        request,
        blueprint,
        first_subcompetency,
    )

    assert "\\n" not in result["explanation"]
    assert "\\n" not in result["worked_example"]
    assert "\\n" not in result["quick_check"]["expected_answer"]
    assert result["explanation"] == "Read the problem\nthen identify the clue."
    assert result["worked_example"] == "A poster says,\nJoin the clean-up drive today!"
    assert result["quick_check"]["expected_answer"] == (
        "The command word shows what to do.\nIt guides the reader clearly."
    )


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_inline_quoted_list_annotations_from_passage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return (
            "{"
            '"title": "Assessment Passage", '
            '"topic_domain": "sustainable fishing", '
            '"genre": "informational", '
            '"passage": ['
            '"Many people depend on fish for food. ["fish for food", "earn a living"] We should protect the sea.", '
            '"Sustainable fishing protects ocean habitats. ["protects ocean habitats"]"'
            "], "
            '"evidence_clues": ['
            '"fish for food", '
            '"protects ocean habitats"'
            "], "
            '"answerability_note": "All questions are answerable from the text."'
            "}"
        )

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "Many people depend on fish for food. We should protect the sea.",
        "Sustainable fishing protects ocean habitats.",
    ]
    assert result["evidence_clues"] == [
        "fish for food",
        "protects ocean habitats",
    ]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_multiline_quoted_list_annotations_from_passage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return """{
    "title": "Assessment Passage",
    "topic_domain": "student nursing infection-control drill",
    "genre": "Explanatory",
    "passage": [
        "Imagine a student nurse, Maria, practicing basic patient care skills in a simulated hospital setting. ["
            "quote one",
            "quote two"
        "]. Her instructor emphasizes standard precautions during every drill. These precautions are the foundation of infection control.",
        "Maria begins by washing her hands thoroughly before touching her patient. ["
            "quote three",
            "quote four"
        "]. She puts on gloves before starting any procedure that might involve contact with blood or bodily fluids."
    ],
    "evidence_clues": [
        "foundation of infection control",
        "washing her hands thoroughly"
    ],
    "answerability_note": "The passage provides clear examples of standard precautions."
}"""

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "Imagine a student nurse, Maria, practicing basic patient care skills in a simulated hospital setting. Her instructor emphasizes standard precautions during every drill. These precautions are the foundation of infection control.",
        "Maria begins by washing her hands thoroughly before touching her patient. She puts on gloves before starting any procedure that might involve contact with blood or bodily fluids.",
    ]
    assert result["evidence_clues"] == [
        "foundation of infection control",
        "washing her hands thoroughly",
    ]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_concatenated_quoted_list_annotations_from_passage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return """{
    "title": "Assessment Passage",
    "topic_domain": "student nursing infection-control drill",
    "genre": "expository",
    "passage": [
        "In a student nursing drill, imagine you're caring for Patient Maria, who has a cough. [" + "\\\"Patient Maria seems stable, but any cough is a potential source of infection,\\\"" + "] notes your instructor, stressing the importance of standard precautions.",
        "Hand hygiene is crucial. [" + "\\\"If soap and water aren't available, use an alcohol-based hand sanitizer,\\\"" + "] your instructor reminds you."
    ],
    "evidence_clues": [
        "standard precautions",
        "alcohol-based hand sanitizer"
    ],
    "answerability_note": "All claims are directly answerable from the text."
}"""

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "In a student nursing drill, imagine you're caring for Patient Maria, who has a cough. notes your instructor, stressing the importance of standard precautions.",
        "Hand hygiene is crucial. your instructor reminds you.",
    ]
    assert result["evidence_clues"] == [
        "standard precautions",
        "alcohol-based hand sanitizer",
    ]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_multi_segment_concatenated_annotations_from_passage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return """{
    "title": "Assessment Passage",
    "topic_domain": "student nursing infection-control drill",
    "genre": "instructive",
    "passage": [
        "Imagine you're a student nurse practicing basic patient care. [" + "evidence_clues" + ": wash your hands" + "] You wash your hands before patient contact.",
        "You prepare sterile supplies. [" + "evidence_clues" + ": maintain asepsis" + "] You avoid touching the catheter itself."
    ],
    "evidence_clues": [
        "wash your hands",
        "maintain asepsis"
    ],
    "answerability_note": "All claims are directly answerable from the text."
}"""

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "Imagine you're a student nurse practicing basic patient care. You wash your hands before patient contact.",
        "You prepare sterile supplies. You avoid touching the catheter itself.",
    ]
    assert result["evidence_clues"] == ["wash your hands", "maintain asepsis"]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_mixed_quote_code_like_annotations_from_passage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return """{
    "title": "Assessment Passage",
    "topic_domain": "student nursing injection drill",
    "genre": "Explanatory",
    "passage": [
        "Maria is a student nurse practicing injections on a mannequin. [" + '"' + "Standard precautions are a set of infection control practices used to prevent transmission of diseases," + '"' + "] she reminds herself.",
        "Before starting, Maria washes her hands. [" + '"' + "She washes her hands thoroughly with soap and water," + '"' + "] then puts on gloves."
    ],
    "evidence_clues": [
        "Standard precautions are a set of infection control practices used to prevent transmission of diseases",
        "She washes her hands thoroughly with soap and water"
    ],
    "answerability_note": "All passage claims are directly attributable to standard nursing practices."
}"""

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "Maria is a student nurse practicing injections on a mannequin. she reminds herself.",
        "Before starting, Maria washes her hands. then puts on gloves.",
    ]
    assert result["evidence_clues"] == [
        "Standard precautions are a set of infection control practices used to prevent transmission of diseases",
        "She washes her hands thoroughly with soap and water",
    ]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_live_style_mixed_quote_concat_annotations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return """{
    \"title\": \"Assessment Passage\",
    \"topic_domain\": \"community clinic handwashing campaign\",
    \"genre\": \"Informative Article\",
    \"passage\": [
        \"Barangay Maligaya's community clinic launched a hand hygiene campaign during flu season. [\" + '\"' + \"Handwashing with soap and water is a simple yet highly effective way to prevent infections,\" + '\"' + \" stated Dr. Reyes, the clinic's head physician. This campaign aims to reduce illness in the barangay.\",
        \"The campaign includes pamphlets and demonstrations. [\" + '\"' + \"Consistent hand hygiene practices are a key component of infection control,\" + '\"' + \" explained Nurse Santos, the lead nurse for the campaign.\"
    ],
    \"evidence_clues\": [
        \"Handwashing with soap and water is a simple yet highly effective way to prevent infections,\",
        \"Consistent hand hygiene practices are a key component of infection control,\"
    ],
    \"answerability_note\": \"The passage provides direct evidence about the effectiveness of handwashing and infection control.\"
}"""

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "Barangay Maligaya's community clinic launched a hand hygiene campaign during flu season. stated Dr. Reyes, the clinic's head physician. This campaign aims to reduce illness in the barangay.",
        "The campaign includes pamphlets and demonstrations. explained Nurse Santos, the lead nurse for the campaign.",
    ]
    assert result["evidence_clues"] == [
        "Handwashing with soap and water is a simple yet highly effective way to prevent infections,",
        "Consistent hand hygiene practices are a key component of infection control,",
    ]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_escaped_quote_concat_annotations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return """{
    \"title\": \"Assessment Passage\",
    \"topic_domain\": \"community clinic campaign\",
    \"genre\": \"Informative\",
    \"passage\": [
        \"The clinic launched a hand hygiene campaign this month. [\\\" + '\"campaign focus\"' + \\\"]. The campaign includes posters and demonstrations.\",
        \"Handwashing is everyone's responsibility. [\\\" + '\"shared responsibility\"' + \\\"]. Patients and visitors are encouraged to sanitize their hands.\"
    ],
    \"evidence_clues\": [
        \"campaign focus\",
        \"shared responsibility\"
    ],
    \"answerability_note\": \"All passage claims are directly attributable to the text.\"
}"""

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "The clinic launched a hand hygiene campaign this month. . The campaign includes posters and demonstrations.",
        "Handwashing is everyone's responsibility. . Patients and visitors are encouraged to sanitize their hands.",
    ]
    assert result["evidence_clues"] == ["campaign focus", "shared responsibility"]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_adjacent_escaped_string_annotations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return """{
    \"title\": \"Assessment Passage\",
    \"topic_domain\": \"community clinic campaign\",
    \"genre\": \"Explanatory\",
    \"passage\": [
        \"The clinic launched a hand hygiene campaign this month. [\\\" \\\"evidence_clues: campaign launch]\",
        \"The goal is to reduce the spread of infections. [\\\" \\\"evidence_clues: reduce infection]\"
    ],
    \"evidence_clues\": [
        \"campaign launch\",
        \"reduce infection\"
    ],
    \"answerability_note\": \"All questions should be answerable from the passage.\"
}"""

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "The clinic launched a hand hygiene campaign this month.",
        "The goal is to reduce the spread of infections.",
    ]
    assert result["evidence_clues"] == ["campaign launch", "reduce infection"]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_double_quote_placeholder_annotations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return """{
    \"title\": \"Assessment Passage\",
    \"topic_domain\": \"hospital emergency room triage\",
    \"genre\": \"narrative\",
    \"passage\": [
        \"Nurse Ella works triage in a busy hospital emergency room. [\"\"quote one\"\"] Many patients arrive with unknown conditions. [\" \"quote two\"\"] Ella must quickly assess each person and decide the order they will see a doctor.\",
        \"Ella knows that any patient could have an infection, even if they don't show obvious signs. That's why she always follows standard precautions. [\" \"quote three\"\"] Before touching each patient, Ella performs hand hygiene.\"
    ],
    \"evidence_clues\": [
        \"Many patients arrive with unknown conditions.\",
        \"That's why she always follows standard precautions.\"
    ],
    \"answerability_note\": \"All passage claims are directly answerable.\"
}"""

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "Nurse Ella works triage in a busy hospital emergency room. Many patients arrive with unknown conditions. Ella must quickly assess each person and decide the order they will see a doctor.",
        "Ella knows that any patient could have an infection, even if they don't show obvious signs. That's why she always follows standard precautions. Before touching each patient, Ella performs hand hygiene.",
    ]
    assert result["evidence_clues"] == [
        "Many patients arrive with unknown conditions.",
        "That's why she always follows standard precautions.",
    ]


@pytest.mark.asyncio
async def test_wave2_section_nodes_strip_unmatched_quote_concat_prefix_annotations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _load_request_from_fixture()
    blueprint = _build_blueprint(request)

    async def fake_call_gemini(**_: object) -> str:
        return """{
    \"title\": \"Assessment Passage\",
    \"topic_domain\": \"home healthcare visit for medication administration\",
    \"genre\": \"Narrative\",
    \"passage\": [
        \"Nena receives home healthcare support for insulin administration. [\\\" + \\\"Rose prepares sterile supplies and performs hand hygiene before the procedure.\",
        \"Rose explains each step, uses gloves, and disposes of sharps safely after injection. [\\\" + \\\"She documents the visit and reinforces infection-control reminders.\"
    ],
    \"evidence_clues\": [
        \"performs hand hygiene before the procedure\",
        \"disposes of sharps safely\"
    ],
    \"answerability_note\": \"All claims are directly answerable from the passage.\"
}"""

    monkeypatch.setattr(sections_module, "call_gemini", fake_call_gemini)

    result = await assessment_passage_module.generate_assessment_passage(
        request, blueprint
    )

    assert result["passage"] == [
        "Nena receives home healthcare support for insulin administration. Rose prepares sterile supplies and performs hand hygiene before the procedure.",
        "Rose explains each step, uses gloves, and disposes of sharps safely after injection. She documents the visit and reinforces infection-control reminders.",
    ]
    assert result["evidence_clues"] == [
        "performs hand hygiene before the procedure",
        "disposes of sharps safely",
    ]
