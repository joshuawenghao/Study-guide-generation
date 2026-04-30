import type { GenerateRequest } from '../types'

export function buildSectionPlannerPrompt(req: GenerateRequest): string {
  const { lesson_metadata, curriculum, instructional_design } = req
  const { subject, grade_level } = lesson_metadata

  return `You are an expert instructional designer. Given the lesson metadata below, decide which sections should be included in the study guide and return a JSON array of SectionSpec objects.

## Lesson Metadata
- Subject: ${subject}
- Grade Level: ${grade_level}
- Unit: ${lesson_metadata.unit_number} — ${lesson_metadata.unit_title}
- Lesson: ${lesson_metadata.lesson_number} — ${lesson_metadata.lesson_title}
- Market: ${lesson_metadata.market}
- Language: ${lesson_metadata.language}

## Curriculum
- Competency Code: ${curriculum.competency_code}
- Competency Description: ${curriculum.competency_description}
- Sub-competencies: ${curriculum.sub_competencies.map((sc) => `${sc.id}: ${sc.label}`).join('; ')}

## Instructional Design
- Core Concept: ${instructional_design.core_concept}
- Bloom Targets: ${instructional_design.bloom_targets.join(', ')}
- Essential Question Seed: ${instructional_design.essential_question_seed}

## Selection Rules (apply all that match)

1. ALWAYS include: intro, learning_targets, key_points, self_assessment, answer_key
2. Include warmup and vocabulary_box for grades 1–9 (grade_level <= 9)
3. Include concept_explainer and subconcept_block for language arts, humanities, social studies subjects
4. Include worked_example (2–3 instances) for mathematics and science subjects
5. Include practice_problems for mathematics subjects
6. Include experiment_design for science subjects with grade_level >= 4
7. Include reading_passage, passage_questions, strategy_list, deep_dive, check_in, assessment_passage, assessment_questions, step_up for language arts and English subjects
8. answer_key must always have depends_on set to ALL other section_ids in the plan
9. assessment_questions must have depends_on: ["assessment_passage"]
10. check_in must have depends_on: ["reading_passage"] if reading_passage is included
11. passage_questions must have depends_on: ["reading_passage"] if both are included
12. step_up must have depends_on: ["assessment_passage", "assessment_questions"] if all three are included
13. Each section_id must be unique. For repeated section types (e.g. worked_example used multiple times), use numeric suffixes: worked_example_1, worked_example_2, worked_example_3
14. For subconcept_block, create one instance per sub_competency, each with config.subconcept_index set to the 0-based index
15. For worked_example instances, set config.difficulty to "basic", "intermediate", or "advanced" respectively, and config.example_number to the instance number
16. For practice_problems, set config.count to 5 by default
17. order values must be 1-based integers in sequential render order

## Important Differentiation Examples
- "Grade 6 Mathematics": include intro, learning_targets, warmup, vocabulary_box, worked_example_1 (basic), worked_example_2 (intermediate), worked_example_3 (advanced), practice_problems, key_points, self_assessment, answer_key
- "Grade 6 English": include intro, learning_targets, warmup, vocabulary_box, concept_explainer, subconcept_block_1..N, reading_passage, passage_questions, strategy_list, deep_dive, check_in, key_points, assessment_passage, assessment_questions, step_up, self_assessment, answer_key
- "Grade 8 Science": include intro, learning_targets, warmup, vocabulary_box, concept_explainer, worked_example_1, worked_example_2, experiment_design, key_points, self_assessment, answer_key

## Output Schema
Return ONLY a JSON array. No prose. Each object in the array must match:
{
  "section_id": "string (unique slug)",
  "section_type": "string (one of: intro, learning_targets, warmup, vocabulary_box, concept_explainer, subconcept_block, worked_example, practice_problems, experiment_design, reading_passage, passage_questions, strategy_list, deep_dive, check_in, key_points, assessment_passage, assessment_questions, step_up, self_assessment, answer_key)",
  "order": "number (1-based render order)",
  "depends_on": ["string"] // omit if no dependencies,
  "config": {} // omit if not needed
}

Now generate the section plan for: ${subject}, Grade ${grade_level}.`
}
