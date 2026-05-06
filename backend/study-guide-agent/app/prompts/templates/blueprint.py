from __future__ import annotations

from app.types import GenerateRequest


def build_prompt(spec, blueprint, request: GenerateRequest) -> str:
    del spec, blueprint

    metadata = request.lesson_metadata
    curriculum = request.curriculum
    design = request.instructional_design
    optional_inputs = request.optional

    vocabulary_seeds = optional_inputs.vocabulary_seeds or []
    if vocabulary_seeds:
        vocabulary_instruction = (
            f"Generate exactly {len(vocabulary_seeds)} vocabulary entries. "
            "Use the teacher-provided seed words as the canonical vocabulary words, "
            "in the same order, and write a definition and example sentence for each one."
        )
        vocabulary_seed_text = "Teacher-provided vocabulary seeds: " + ", ".join(vocabulary_seeds)
    else:
        vocabulary_instruction = (
            "Generate exactly 5 vocabulary entries. Choose words that are central to the "
            "lesson and likely to appear across the later study guide sections."
        )
        vocabulary_seed_text = "Teacher-provided vocabulary seeds: none"

    topic_domain_hints = optional_inputs.topic_domains or {}
    if topic_domain_hints:
        topic_domain_text = "Optional topic domain hints:\n" + "\n".join(
            f"- {key}: {value}" for key, value in topic_domain_hints.items()
        )
    else:
        topic_domain_text = "Optional topic domain hints: none"

    sub_competency_text = "\n".join(
        f"- {item.id}: {item.label}" for item in curriculum.sub_competencies
    )

    essential_question_instruction = (
        "Build a full essential question from this seed: "
        f'"{design.essential_question_seed}". The result must be one complete, '
        "student-facing question that is clear, open-ended, and aligned to the lesson."
    )

    blueprint_schema = """{
  "lesson_id": "string",
  "title": "string",
  "essential_question": "string",
  "introduction_hook": "string",
  "learning_targets": [
    {
      "number": 1,
      "bloom_verb": "string",
      "objective": "string"
    }
  ],
  "vocabulary": [
    {
      "word": "string",
      "definition": "string",
      "example_sentence": "string"
    }
  ],
  "topic_domains": {
    "model_passage": "string",
    "assessment_passage": "string",
    "entertain_example": "string",
    "inform_example": "string",
    "persuade_example": "string"
  },
  "sub_competencies": [
    {
      "id": "string",
      "label": "string"
    }
  ],
  "core_concept": "string"
}"""

    prompt_lines = [
        "Create the blueprint JSON for a curriculum-aligned K-12 study guide.",
        "Lesson context:",
        f"- Lesson title: {metadata.lesson_title}",
        f"- Grade level: {metadata.grade_level}",
        f"- Subject: {metadata.subject}",
        f"- Market: {metadata.market}",
        f"- Competency code: {curriculum.competency_code}",
        f"- Competency description: {curriculum.competency_description}",
        f"- Unit title: {metadata.unit_title}",
        f"- Lesson code: {metadata.lesson_code}",
        f"- Core concept: {design.core_concept}",
        f"- Tone register: {optional_inputs.tone_register}",
        f"- Length preset: {optional_inputs.length_preset.value}",
        "Sub-competencies:",
        sub_competency_text,
        vocabulary_seed_text,
        topic_domain_text,
        essential_question_instruction,
        (
            "Produce exactly 3 learning_targets derived from the provided bloom_targets. "
            "Each objective must be student-facing, measurable, and clearly phrased in a way "
            "a learner can understand."
        ),
        (
            "Use these Bloom targets in order when writing the learning targets: "
            f"{design.bloom_targets[0]}, {design.bloom_targets[1]}, {design.bloom_targets[2]}."
        ),
        vocabulary_instruction,
        (
            "Set topic_domains.model_passage and topic_domains.assessment_passage to DIFFERENT "
            "topic domains. They must not overlap, paraphrase each other, or name the same "
            "real-world context."
        ),
        (
            "Also fill entertain_example, inform_example, and persuade_example with distinct, "
            "instructionally useful topic domains that support later writing tasks."
        ),
        (
            "Set sub_competencies to the same ordered list provided in the request and copy "
            "core_concept directly from the request."
        ),
        "Expected Blueprint JSON schema:",
        blueprint_schema,
        "Return only JSON.",
    ]

    return "\n".join(prompt_lines)