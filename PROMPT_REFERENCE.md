# Prompt Reference — Study Guide Generator

This document shows the exact prompts sent to the model for each section of the study guide. Use it as a baseline when tuning prompts via the Prompt Lab.

---

## How the Prompt Lab works

Every generation runs two prompts per section:

1. **System prompt** — always sent; sets the model's persona, market, grade, and global formatting rules
2. **Section user prompt** — specific instructions for that section plus the relevant context (blueprint values, upstream section content, etc.)

In the Prompt Lab you can append extra instructions to either:

- **System prompt append** — extra rules added to the bottom of the shared system prompt, affecting all sections
- **Section override** (keyed by section name) — extra instructions appended to the bottom of that section's user prompt

Your override text is appended verbatim after a separator line like:
> "Prompt-lab reviewer override for this section: Follow the additional instructions below while preserving the existing JSON schema and all other output constraints."

The JSON schema and structural requirements are **not** overridable — the model is always told to return valid JSON matching the defined schema.

> **Note:** The blueprint section (which generates the shared foundation before any section runs) does **not** have a section-level override key. To influence blueprint generation, use the system prompt append.

---

## Dynamic values

Throughout this document, values filled in at runtime from the teacher's lesson form or the generated blueprint are shown in **`« »`** markers, e.g. `«lesson_title»`. These are substituted automatically — you do not need to include them in your override.

---

## System Prompt

Sent once per generation request. Shared by all section calls.

**What varies at runtime:** `«market»`, `«grade_level»`, `«subject»`, and the reading-level guidance paragraph (derived from grade level).

```
You are an expert curriculum-aligned study guide writer for «market» Grade «grade_level» «subject».

Write for learners in the «market» market and keep all explanations appropriate for Grade «grade_level» «subject».

Reading level guidance: «grade-derived guidance — see table below»

Voice rules: Maintain a warm, clear, and encouraging teaching voice. Never sound condescending, sarcastic, or patronizing.

Cultural relevance: Use names, situations, references, and examples that feel natural and contextually appropriate for learners in «market». Avoid irrelevant cultural assumptions from other markets unless the request explicitly requires them.

Formatting rules: Return valid JSON only. Do not wrap the response in markdown code fences. Do not add commentary, headings, or prose outside the JSON object.

Markup rule: Do not include HTML or XML tags such as <b>, <i>, <br>, or <p> anywhere in any JSON string value. Return plain text only.

Readability target: Aim for a Flesch-Kincaid reading level close to Grade «grade_level». Prefer common everyday words when possible, keep most sentences to one clear idea, and avoid extra clauses or abstract academic phrasing unless a lesson term requires it.

Age-fit rule: Keep the material intellectually appropriate for the target grade even when the language is simple. Do not make older-student content sound childish or written for much younger learners.

Sentence discipline: Keep sentences concise. For upper elementary and middle school outputs, default to short-to-medium sentences and define new academic terms in plain language immediately when they first appear.

Output discipline: Follow the requested structure exactly, keep every field machine-parseable, and do not invent extra top-level keys, side notes, or explanatory text outside the required JSON schema.

[Math only] Math notation rule: Use plain-text math notation such as 3/4, 1/2, 4 x 6, or x + 3. Do not use LaTeX commands, backslashes, or escaped control sequences in the JSON output.
```

**Reading-level guidance by grade band:**

| Grade | Guidance inserted |
|-------|------------------|
| ≤ 2 | Use very short sentences, concrete vocabulary, and direct explanations that support early readers. |
| 3–5 | Use clear grade-appropriate vocabulary, mostly short-to-medium sentences, and concrete examples before abstraction. |
| 6–8 | Use accessible academic language, varied sentence length, and explanations that assume developing independence with subject vocabulary. |
| 9–10 | Use solid secondary-school academic language, precise terminology, and explanations that remain readable without becoming simplistic. |
| 11–12 | Use advanced secondary-school academic language with precise subject terminology, but keep explanations plain, concrete, and efficient enough for first-pass student reading. When a technical term is necessary, define it in simpler words nearby instead of building long, dense sentences. |

**Prompt Lab override key:** *(system-level — use "System prompt append" field)*

---

## Blueprint Prompt

Runs first. Its output — title, essential question, learning targets, vocabulary, topic domains, sub-competencies — feeds every section prompt.

**Prompt Lab override key:** *(none — use system prompt append to influence blueprint generation)*

**Context provided at runtime:**
- Lesson title, grade level, subject, market, unit title, lesson code
- Competency code and description
- Sub-competency list (id + label for each)
- Core concept, Bloom targets (3 levels), essential question seed
- Tone register, length preset
- Vocabulary seeds (if provided by teacher, otherwise empty)
- Topic domain hints (if provided by teacher, otherwise empty)

**Prompt sent to model:**

```
Create the blueprint JSON for a curriculum-aligned K-12 study guide.

Lesson context:
- Lesson title: «lesson_title»
- Grade level: «grade_level»
- Subject: «subject»
- Market: «market»
- Competency code: «competency_code»
- Competency description: «competency_description»
- Unit title: «unit_title»
- Lesson code: «lesson_code»
- Core concept: «core_concept»
- Tone register: «tone_register»
- Length preset: «length_preset»

Sub-competencies:
- «sub_competency_id»: «sub_competency_label»
[... one line per sub-competency]

Teacher-provided vocabulary seeds: «seed_words, comma-separated — or "none"»
Optional topic domain hints: «domain hints — or "none"»

Build a full essential question from this seed: "«essential_question_seed»". The result must be one complete, student-facing question that is clear, open-ended, and aligned to the lesson.

Produce exactly 3 learning_targets derived from the provided bloom_targets. Each objective must be student-facing, measurable, and clearly phrased in a way a learner can understand.

Use these Bloom targets in order when writing the learning targets: «bloom_target_1», «bloom_target_2», «bloom_target_3».

[If vocabulary seeds provided:]
Generate exactly «N» vocabulary entries. Use the teacher-provided seed words as the canonical vocabulary words, in the same order, and write a definition and example sentence for each one.

[If no vocabulary seeds:]
Generate exactly 5 vocabulary entries. Choose words that are central to the lesson and likely to appear across the later study guide sections.

Set topic_domains.model_passage and topic_domains.assessment_passage to DIFFERENT topic domains. They must not overlap, paraphrase each other, or name the same real-world context.

Also fill entertain_example, inform_example, and persuade_example with distinct, instructionally useful topic domains that support later writing tasks.

Set sub_competencies to the same ordered list provided in the request and copy core_concept directly from the request.

Expected Blueprint JSON schema:
{
  "lesson_id": "string",
  "title": "string",
  "essential_question": "string",
  "introduction_hook": "string",
  "learning_targets": [
    { "number": 1, "bloom_verb": "string", "objective": "string" }
  ],
  "vocabulary": [
    { "word": "string", "definition": "string", "example_sentence": "string" }
  ],
  "topic_domains": {
    "model_passage": "string",
    "assessment_passage": "string",
    "entertain_example": "string",
    "inform_example": "string",
    "persuade_example": "string"
  },
  "sub_competencies": [
    { "id": "string", "label": "string" }
  ],
  "core_concept": "string"
}

Return only JSON.
```

---

## Section Prompts

Sections are organized by the wave in which they are generated.

---

### Wave 1 — Generated in parallel (no cross-section dependencies)

---

#### Introduction (`intro`)

Generates the opening section of the study guide.

**Prompt Lab override key:** `intro`

**Context from blueprint:** title, essential question, introduction hook, core concept, learning targets

**Prompt sent to model:**

```
Create the introduction section for a K-12 study guide.
Use the blueprint as the single source of truth.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Introduction hook: «blueprint.introduction_hook»
- Core concept: «blueprint.core_concept»
- Learning targets:
  - 1. «target_1_objective»
  - 2. «target_2_objective»
  - 3. «target_3_objective»

Requirements:
- Write a warm, student-facing opening linked directly to the essential question.
- Use the hook as the first attention-grabbing idea, but rewrite it as polished study-guide prose.
- Provide exactly 2 concise paragraphs that prepare students for the lesson.
- [Grade ≤ 5] Keep each paragraph to 1 or 2 short sentences, and use everyday classroom words before academic phrasing.
- [Grade ≥ 6] Keep both paragraphs concise and focused on one main idea each.
- Make the bridge_to_lesson explain how the opening connects to the study guide work ahead.

Expected JSON schema:
{
  "title": "Introduction",
  "hook": "string",
  "essential_question": "string",
  "paragraphs": ["string"],
  "bridge_to_lesson": "string"
}

Return only JSON.
```

---

#### Learning Targets (`learning_targets`)

Generates the student-facing learning targets section with "I can" framing and success look-fors.

**Prompt Lab override key:** `learning_targets`

**Context from blueprint:** title, lesson_id, core concept, learning targets (number, bloom_verb, objective)

**Prompt sent to model:**

```
Create the learning targets section for a K-12 study guide.
Use the blueprint learning targets directly and keep them student-facing.
- Lesson title: «blueprint.title»
- Lesson id: «blueprint.lesson_id»
- Core concept: «blueprint.core_concept»
- Blueprint learning targets:
  - 1. «bloom_verb»: «objective»
  - 2. «bloom_verb»: «objective»
  - 3. «bloom_verb»: «objective»

Requirements:
- Preserve the same number and order as the blueprint learning targets.
- Keep each objective aligned to the blueprint wording and clearly usable as an "I can" statement.
- Add a short success_look_for that describes what evidence of learning would look like.
- Keep the section focused on competency and student-facing goals only.

Expected JSON schema:
{
  "title": "Learning Targets",
  "competency_focus": {
    "lesson_id": "string",
    "core_concept": "string"
  },
  "targets": [
    {
      "number": 1,
      "bloom_verb": "string",
      "objective": "string",
      "success_look_for": "string"
    }
  ]
}

Return only JSON.
```

---

#### Warm-Up (`warmup`)

Generates a short (~5 min) activation activity for teachers to use before the main lesson.

**Prompt Lab override key:** `warmup`

**Context from blueprint:** title, essential question, introduction hook, core concept

**Prompt sent to model:**

```
Create the warm-up section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Introduction hook: «blueprint.introduction_hook»
- Core concept: «blueprint.core_concept»

Requirements:
- Design one short activation activity that can be completed in about 5 minutes.
- Use the hook and essential question to activate prior knowledge.
- Include a clear purpose statement explaining why the warm-up matters for the lesson.
- Provide student_instructions as a short ordered sequence the learner can follow.
- Keep the activity lightweight, classroom-ready, and aligned to the lesson focus.

Expected JSON schema:
{
  "title": "Warm-Up",
  "activity_type": "string",
  "purpose": "string",
  "student_instructions": ["string"],
  "teacher_tip": "string",
  "estimated_minutes": 5
}

Return only JSON.
```

---

#### Vocabulary (`vocabulary`)

Generates the vocabulary table section directly from the blueprint's canonical word list.

**Prompt Lab override key:** `vocabulary`

**Context from blueprint:** title, core concept, vocabulary entries (word, definition, example_sentence)

**Prompt sent to model:**

```
Create the vocabulary section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Core concept: «blueprint.core_concept»
- Canonical vocabulary entries from the blueprint:
  - «word»: «definition» Example: «example_sentence»
  [... one line per vocabulary word]

Requirements:
- Return exactly one entry for each blueprint vocabulary word, in the same order.
- Copy each word exactly so downstream validators can track vocabulary usage across the guide.
- Add a classroom-appropriate part_of_speech for each word.
- Keep definitions and example sentences aligned to the lesson context.
- Do not invent extra vocabulary words or omit any blueprint word.

Expected JSON schema:
{
  "title": "Vocabulary",
  "entries": [
    {
      "word": "string",
      "part_of_speech": "string",
      "definition": "string",
      "example_sentence": "string"
    }
  ]
}

Return only JSON.
```

---

#### Key Points (`key_points`)

Generates one concise summary statement per sub-competency for end-of-lesson review.

**Prompt Lab override key:** `key_points`

**Context from blueprint:** title, essential question, core concept, sub-competencies (id + label)

**Prompt sent to model:**

```
Create the key points section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Core concept: «blueprint.core_concept»
- Sub-competencies:
  - «sub_competency_id»: «sub_competency_label»
  [... one line per sub-competency]

Requirements:
- Write one numbered summary statement per sub-competency.
- Keep statements concise, clear, and directly aligned to the listed sub-competencies.
- Use the same order as the blueprint sub-competencies.
- Make each statement suitable for quick review at the end of the lesson.

Expected JSON schema:
{
  "title": "Key Points",
  "points": [
    {
      "number": 1,
      "sub_competency_id": "string",
      "sub_competency_label": "string",
      "statement": "string"
    }
  ]
}

Return only JSON.
```

---

#### Self-Assessment (`self_assessment`)

Generates a self-assessment rubric table. Each row's `skill` value is validated to match the corresponding learning target objective **verbatim** — this is a hard validator, so changing the skill wording via an override will cause validation failure.

**Prompt Lab override key:** `self_assessment`

**Context from blueprint:** title, essential question, learning targets (objectives only)

**Prompt sent to model:**

```
Create the self-assessment section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Learning target objectives that must be used verbatim as skill values:
  - «target_1_objective»
  - «target_2_objective»
  - «target_3_objective»

Requirements:
- Create one row per blueprint learning target, in the same order.
- Each rows.skill value must match the corresponding learning target objective verbatim.
- Use exactly these confidence levels: Not yet, Getting there, Confident.
- Add a brief reflection_prompt that helps a learner judge their own evidence of success.
- Do not rewrite, shorten, or paraphrase the skill text.

Expected JSON schema:
{
  "title": "Self-Assessment",
  "confidence_levels": ["Not yet", "Getting there", "Confident"],
  "rows": [
    {
      "skill": "string",
      "reflection_prompt": "string"
    }
  ]
}

Return only JSON.
```

> **Validator note:** A hard validator checks that each `skill` value matches a blueprint learning target objective verbatim. Overrides that instruct the model to rephrase skill text will cause validation failure and trigger a retry.

---

### Wave 2 — Generated in parallel (depend only on blueprint)

---

#### Core Explainer (`core_explainer`)

Generates the main instructional explanation section, one explained point per sub-competency.

**Prompt Lab override key:** `core_explainer`

**Context from blueprint:** title, essential question, core concept, sub-competencies (id + label)

**Prompt sent to model:**

```
Create the core explainer section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Core concept: «blueprint.core_concept»
- Sub-competencies to cover:
  - «sub_competency_id»: «sub_competency_label»
  [... one line per sub-competency]

Requirements:
- Write a clear overview that explains the lesson's core concept in student-friendly language.
- Include one explained point per sub-competency in the same order as the blueprint.
- Connect each explanation to a concrete real-world or classroom-relevant example.
- Keep the section explanatory rather than quiz-like.
- Keep the reading level close to Grade «grade_level».
- Use short-to-medium sentences and plain classroom vocabulary.
- Keep the overview to 2 or 3 short sentences, and keep each explanation focused on one main idea.
- Avoid stacked clauses or abstract wording when a simpler sentence will do.

Expected JSON schema:
{
  "title": "Core Explainer",
  "overview": "string",
  "explained_points": [
    {
      "sub_competency_id": "string",
      "sub_competency_label": "string",
      "explanation": "string",
      "real_world_connection": "string"
    }
  ],
  "closing_summary": "string"
}

Return only JSON.
```

---

#### Sub-Concept (`subconcept`)

Generated once per sub-competency (e.g. 3 sub-competencies → 3 separate calls). Each call targets a single sub-competency with a worked example and quick-check question.

**Prompt Lab override key:** `subconcept`

**Context from blueprint:** title, essential question, core concept + the specific sub-competency being generated

**Prompt sent to model:**

```
Create one sub-concept section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Core concept: «blueprint.core_concept»
- Target sub-competency id: «sub_competency_id»
- Target sub-competency label: «sub_competency_label»

Requirements:
- Focus only on the provided sub-competency.
- Explain the sub-concept clearly in student-facing language.
- Include one worked_example that directly illustrates the target sub-competency.
- Include one quick_check with a short expected answer to confirm understanding.
- Keep the reading level close to Grade «grade_level».
- Use short sentences and concrete examples that a student can picture quickly.
- Keep the explanation and worked_example direct rather than academic or abstract.

Expected JSON schema:
{
  "title": "string",
  "sub_competency_id": "string",
  "sub_competency_label": "string",
  "explanation": "string",
  "worked_example": "string",
  "quick_check": {
    "question": "string",
    "expected_answer": "string"
  }
}

Return only JSON.
```

> **Note:** The override for `subconcept` applies to every sub-competency call in a given run — there is no per-sub-competency override.

---

#### Strategy List (`strategy_list`)

Generates 3 practical reading or thinking strategies relevant to the lesson's core concept.

**Prompt Lab override key:** `strategy_list`

**Context from blueprint:** title, essential question, core concept

**Prompt sent to model:**

```
Create the strategy list section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Core concept: «blueprint.core_concept»

Requirements:
- Provide 3 practical reading or thinking strategies that help students succeed with this lesson.
- Each strategy must include when_to_use and a short ordered steps list.
- Keep the strategies directly tied to the lesson's core concept and purpose-identification work.
- Keep the reading level close to Grade «grade_level».

Expected JSON schema:
{
  "title": "Strategy List",
  "strategies": [
    {
      "name": "string",
      "when_to_use": "string",
      "steps": ["string"]
    }
  ]
}

Return only JSON.
```

---

#### Deep Dive (`deep_dive`)

Compares how entertain, inform, and persuade differ using the three blueprint-assigned topic domains.

**Prompt Lab override key:** `deep_dive`

**Context from blueprint:** title, core concept, topic_domains (entertain_example, inform_example, persuade_example)

**Prompt sent to model:**

```
Create the deep dive section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Core concept: «blueprint.core_concept»
- Topic domains for rhetorical examples:
  - entertain_example: «blueprint.topic_domains.entertain_example»
  - inform_example: «blueprint.topic_domains.inform_example»
  - persuade_example: «blueprint.topic_domains.persuade_example»

Requirements:
- Compare how entertain, inform, and persuade differ in purpose.
- Use the blueprint example domains directly so the examples stay distinct.
- Include signal_words lists that help students notice clues in texts.
- Keep the reading level close to Grade «grade_level».
- [Grade ≤ 5] Keep compare_focus and takeaway to one short sentence each, and keep every example explanation to one short sentence followed by simple signal words.
- [Grade ≥ 6] Keep compare_focus brief, write each explanation in 1 or 2 short sentences, and keep the takeaway to one short summary sentence.
- Use plain language to contrast the three purposes.

Expected JSON schema:
{
  "title": "Deep Dive",
  "compare_focus": "string",
  "examples": [
    {
      "mode": "string",
      "topic_domain": "string",
      "explanation": "string",
      "signal_words": ["string"]
    }
  ],
  "takeaway": "string"
}

Return only JSON.
```

---

#### Model Passage (`model_passage`)

Generates a practice reading passage for the Check-In questions. **Downstream dependency:** Check-In and Answer Key both use this section's output.

**Prompt Lab override key:** `model_passage`

**Context from blueprint:** title, essential question, topic_domains.model_passage, core concept

**Prompt sent to model:**

```
Create the model passage section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Topic domain for this passage: «blueprint.topic_domains.model_passage»
- Core concept: «blueprint.core_concept»

Requirements:
- Use the assigned model_passage topic domain exactly as the context for the passage.
- Write an evidence-friendly passage that makes the author's purpose inferable from the text.
- Return the passage as an ordered list of paragraphs.
- Include text_features students can notice while reading.
- Keep the passage readable for Grade «grade_level» students.
- [SHORT preset or grade ≤ 4] Write 2 short paragraphs with mostly simple sentence structures.
- [LONG preset or grade ≥ 9] Write 3 concise paragraphs with clear sentence variety, while keeping the passage readable for the target grade.
- [default] Write 2 or 3 concise paragraphs with clear, readable sentence structures.
- Prefer familiar words and concrete details over descriptive flourish.
- Keep most sentences to one clear idea and avoid long dependent clauses.

Expected JSON schema:
{
  "title": "Model Passage",
  "topic_domain": "string",
  "genre": "string",
  "passage": ["string"],
  "text_features": ["string"],
  "evidence_focus": "string"
}

Return only JSON.
```

> **Downstream dependency:** If model_passage is regenerated during a retry, Check-In and Answer Key are also regenerated automatically.

---

#### Assessment Passage (`assessment_passage`)

Generates the assessment reading passage. Must use a different topic domain than the model passage. **Downstream dependency:** Assessment Questions, Step Up, and Answer Key all use this section's output.

**Prompt Lab override key:** `assessment_passage`

**Context from blueprint:** title, essential question, topic_domains.assessment_passage, topic_domains.model_passage (as the domain to avoid), core concept

**Prompt sent to model:**

```
Create the assessment passage section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Topic domain for this passage: «blueprint.topic_domains.assessment_passage»
- Model passage topic domain to avoid: «blueprint.topic_domains.model_passage»
- Core concept: «blueprint.core_concept»

Requirements:
- Use the assigned assessment_passage topic domain exactly and keep it different from the model passage domain.
- Write an evidence-friendly passage suitable for downstream assessment questions and answer-key quotation checks.
- Include evidence_clues that point to phrases students can quote or cite.
- Return the passage as an ordered list of paragraphs.
- Do not append bracketed notes, clue lists, or inline annotations such as ["quote one", "quote two"] inside any passage paragraph.
- Never split one passage paragraph across multiple JSON strings or insert placeholder quote fragments between string segments.
- Never use code-like concatenation, escaped quote snippets, or placeholder expressions inside passage text.
- Keep the passage readable for Grade «grade_level» students.
- [SHORT preset or grade ≤ 4] Write 2 short paragraphs with direct wording and mostly simple sentence structures.
- [LONG preset or grade ≥ 9] Write 3 concise paragraphs with direct wording and clear sentence variety, while keeping the passage readable for the target grade.
- [default] Write 2 or 3 concise paragraphs with direct wording and readable sentence structures.
- Prefer familiar words, concrete details, and short sentences with one main idea each.
- Avoid dense informational phrasing unless a lesson term requires it.

Expected JSON schema:
{
  "title": "Assessment Passage",
  "topic_domain": "string",
  "genre": "string",
  "passage": ["string"],
  "evidence_clues": ["string"],
  "answerability_note": "string"
}

Return only JSON.
```

> **Validator note:** A hard validator checks that model_passage and assessment_passage topic domains differ. Overrides that encourage similar topics may trigger this validator.
>
> **Downstream dependency:** If assessment_passage is regenerated during a retry, Assessment Questions, Step Up, and Answer Key are also regenerated automatically.

---

### Wave 3 — Sequential (each depends on the prior section's output)

---

#### Check-In (`check_in`)

Generates 3 evidence-based questions for the model passage. Depends on model_passage output.

**Prompt Lab override key:** `check_in`

**Context from model_passage output:** passage title, full passage text, text_features, evidence_focus

**Prompt sent to model:**

```
Create the check-in section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Source passage title: «model_passage.title»
- Evidence focus: «model_passage.evidence_focus»
- Source passage text:
  «model_passage.passage — full text»
- Source text features:
  - «text_feature_1»
  - «text_feature_2»
  [... one line per text feature]

Requirements:
- Write 3 short questions that require evidence from the provided passage text.
- Make each evidence_hint point students toward a specific clue or phrase in the passage.
- Keep the questions aligned to the lesson's core concept and author-purpose analysis.
- Keep the reading demand close to Grade «grade_level».

Expected JSON schema:
{
  "title": "Check-In",
  "passage_title": "string",
  "questions": [
    {
      "number": 1,
      "question": "string",
      "evidence_hint": "string",
      "expected_response_type": "string"
    }
  ]
}

Return only JSON.
```

---

#### Assessment Questions (`assessment_questions`)

Generates 4 evidence-based questions for the assessment passage. Depends on assessment_passage output.

**Prompt Lab override key:** `assessment_questions`

**Context from assessment_passage output:** passage title, full passage text, evidence_clues

**Prompt sent to model:**

```
Create the assessment questions section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Source passage title: «assessment_passage.title»
- Source passage text:
  «assessment_passage.passage — full text»
- Evidence clues provided with the passage:
  - «evidence_clue_1»
  - «evidence_clue_2»
  [... one line per evidence clue]

Requirements:
- Write 4 assessment questions that require evidence from the provided passage.
- Make the questions answerable from the passage alone, not outside knowledge.
- Do not introduce a new scenario, patient, procedure, or fact that is not explicitly present in the provided passage.
- Use the same question format as the check-in section: each question must include only question, evidence_hint, and expected_response_type.
- Make each evidence_hint point students toward a specific clue or phrase in the passage without quoting the full answer for them.
- Use display-friendly expected_response_type labels such as Short answer, Multiple choice, or Paragraph response.
- If a question asks students to explain the author's purpose or reasoning in their own words, use Short answer unless answer choices are explicitly written into the question.
- Keep the set suitable for downstream step-up and answer-key generation.
- Keep the reading demand close to Grade «grade_level».

Expected JSON schema:
{
  "title": "Assessment Questions",
  "passage_title": "string",
  "questions": [
    {
      "number": 1,
      "question": "string",
      "evidence_hint": "string",
      "expected_response_type": "string"
    }
  ]
}

Return only JSON.
```

---

#### Step Up (`step_up`)

Generates one higher-order challenge prompt building on the assessment questions. Depends on assessment_passage and assessment_questions output.

**Prompt Lab override key:** `step_up`

**Context from upstream sections:** assessment_passage (title + full text), assessment_questions (question list)

**Prompt sent to model:**

```
Create the step-up section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»
- Assessment passage title: «assessment_passage.title»
- Assessment passage text:
  «assessment_passage.passage — full text»
- Upstream assessment questions:
  - Q1: «question_text»
  - Q2: «question_text»
  [... one line per question]

Requirements:
- Write one higher-order challenge_prompt that builds on the assessment questions.
- Make the prompt require evidence from the assessment passage rather than opinion alone.
- Include required_evidence and success_criteria lists that make expectations explicit.
- Keep the reading demand close to Grade «grade_level».

Expected JSON schema:
{
  "title": "Step Up",
  "challenge_prompt": "string",
  "required_evidence": ["string"],
  "success_criteria": ["string"]
}

Return only JSON.
```

---

### Final Section

---

#### Answer Key (`answer_key`)

Generates model answers with verbatim evidence quotes for check-in, assessment, and step-up sections. Depends on check_in, model_passage, assessment_passage, assessment_questions, and step_up output.

**Prompt Lab override key:** `answer_key`

**Context from upstream sections:** all question sections plus both passages (full text used to build a quote bank)

**Prompt sent to model:**

```
Create the answer key section for a K-12 study guide.
- Lesson title: «blueprint.title»
- Essential question: «blueprint.essential_question»

- Model passage text for check-in answers:
  «model_passage.passage — full text»

- Exact quote bank for check-in answers (choose exactly one per question):
  - "«quote_1»"
  - "«quote_2»"
  [... up to 8 quotes derived from model passage sentences and evidence clues]

- Check-in questions:
  Q«n»: «question»
    - Evidence hint: «evidence_hint»
    - Expected response type: «expected_response_type»
  [... one block per check-in question]

- Assessment passage text:
  «assessment_passage.passage — full text»

- Exact quote bank for assessment answers (use only these exact strings when you quote evidence):
  - "«quote_1»"
  - "«quote_2»"
  [... up to 8 quotes derived from assessment passage sentences and evidence clues]

- Assessment questions:
  - Q«n»: «question»
    - Evidence hint: «evidence_hint»
    - Expected response type: «expected_response_type»
  [... one block per assessment question]

- Step-up prompt:
  «step_up.challenge_prompt»

- Step-up required evidence:
  - «required_evidence_item_1»
  [... one line per required evidence item]

Requirements:
- Provide one answer-key entry per check-in question.
- For check_in_answers, use the model passage text above as the sole source of truth.
- For each check_in_answers entry, choose exactly one evidence_quote from the check-in quote bank above and copy it verbatim.
- Use the evidence hint to choose the most specific supporting quote before writing possible_answer.
- Do not reuse a generic check-in evidence_quote for multiple different questions when a more specific quote is available.
- Keep check_in_answers in the exact same order as the check-in questions above.
- Copy each check_in_answers.question_number and check_in_answers.question exactly from the check-in questions above.
- Answer only the specific check-in question attached to that entry; never swap or reuse an answer for a different check-in question.
- Provide one assessment_answers entry per assessment question.
- Keep assessment_answers in the exact same order as the assessment questions above.
- Copy each assessment_answers.question_number and assessment_answers.question exactly from the assessment questions above.
- For each assessment_answers entry, write possible_answer as a concise model answer to the question itself.
- Match the specificity of the check-in answers: answer the full assessment question directly instead of reducing it to a generic passage-summary sentence.
- Use the assessment question's evidence_hint and expected_response_type to keep the answer aligned to the student-facing prompt.
- Do not write generic meta-instructions such as "The correct answer should..." or "Respond directly to the question." Write the actual answer instead.
- Keep the exact quoted evidence only in evidence_quote. Do not repeat the exact evidence_quote inside possible_answer.
- For each assessment_answers entry, choose exactly one evidence_quote from the assessment quote bank above and copy it verbatim.
- Do not place raw double-quoted evidence inside free-text fields such as check-in answers, step_up_answer.challenge_response, or teacher_note.
- Provide a step_up_answer object that answers the step-up prompt directly and repeats the required_evidence list.
- Keep answers concise, student-appropriate, and structurally ready for downstream quote validation.

Expected JSON schema:
{
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
    "required_evidence": ["string"]
  },
  "teacher_note": "string"
}

Return only JSON.
```

> **Validator note:** A hard validator checks that each `assessment_answers[].evidence_quote` is a substring of the assessment passage body. Overrides that instruct the model to use paraphrased or invented quotes will cause validation failure and trigger a retry.

---

## Quick Reference: Section → Override Key

| Section | Override key | Wave | Hard validator |
|---------|-------------|------|----------------|
| System prompt (global) | *(system prompt append)* | — | — |
| Blueprint | *(no section override; use system append)* | — | JSON schema |
| Introduction | `intro` | 1 | JSON schema |
| Learning Targets | `learning_targets` | 1 | JSON schema |
| Warm-Up | `warmup` | 1 | JSON schema |
| Vocabulary | `vocabulary` | 1 | JSON schema, vocab presence |
| Key Points | `key_points` | 1 | JSON schema |
| Self-Assessment | `self_assessment` | 1 | JSON schema, skill = learning target verbatim |
| Core Explainer | `core_explainer` | 2 | JSON schema |
| Sub-Concept | `subconcept` | 2 | JSON schema |
| Strategy List | `strategy_list` | 2 | JSON schema |
| Deep Dive | `deep_dive` | 2 | JSON schema |
| Model Passage | `model_passage` | 2 | JSON schema |
| Assessment Passage | `assessment_passage` | 2 | JSON schema, domain ≠ model passage |
| Check-In | `check_in` | 3 | JSON schema |
| Assessment Questions | `assessment_questions` | 3 | JSON schema |
| Step Up | `step_up` | 3 | JSON schema |
| Answer Key | `answer_key` | final | JSON schema, evidence quotes verbatim in passage |
