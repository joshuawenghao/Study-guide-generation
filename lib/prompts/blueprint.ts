import type { GenerateRequest, SectionPlan } from '../types'

export function buildBlueprintPrompt(req: GenerateRequest, plan: SectionPlan): string {
  const { lesson_metadata, curriculum, instructional_design, optional } = req
  const sectionTypes = new Set(plan.map((s) => s.section_type))

  const hasReadingPassage = sectionTypes.has('reading_passage')
  const hasAssessmentPassage = sectionTypes.has('assessment_passage')
  const hasWorkedExample = sectionTypes.has('worked_example')

  let topicDomainsInstructions = `Populate topic_domains as a key-value object based on the sections in the plan.`

  if (hasReadingPassage || hasAssessmentPassage) {
    topicDomainsInstructions += `
- Since reading_passage is in the plan: include "model_passage" key with a specific topic suitable for a model reading passage.
- Since assessment_passage is in the plan: include "assessment_passage" key with a DIFFERENT topic from model_passage, still relevant to the lesson.`
  }

  if (hasWorkedExample) {
    topicDomainsInstructions += `
- Since worked_example is in the plan: include "worked_example" key with the mathematical/scientific context for examples.`
  }

  if (!hasReadingPassage && !hasAssessmentPassage && !hasWorkedExample) {
    topicDomainsInstructions += `
- Include at least one topic domain relevant to the core concept of this lesson.`
  }

  const vocabInstruction =
    optional?.vocabulary_seeds && optional.vocabulary_seeds.length > 0
      ? `Use exactly these vocabulary seeds as the basis for your vocabulary list: ${optional.vocabulary_seeds.join(', ')}. Generate a full entry for each.`
      : `Generate exactly 5 vocabulary words that are key to understanding this lesson. Choose words appropriate for Grade ${lesson_metadata.grade_level}.`

  return `Generate the canonical shared blueprint JSON for this lesson. All section generators will read from this blueprint.

## Lesson Metadata
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}
- Language: ${lesson_metadata.language}
- Unit: ${lesson_metadata.unit_number} — ${lesson_metadata.unit_title}
- Lesson: ${lesson_metadata.lesson_number} — ${lesson_metadata.lesson_title}
- Lesson Code: ${lesson_metadata.lesson_code}

## Curriculum
- Competency Code: ${curriculum.competency_code}
- Competency Description: ${curriculum.competency_description}
- Sub-competencies: ${curriculum.sub_competencies.map((sc) => `${sc.id}: ${sc.label}`).join('; ')}

## Instructional Design
- Core Concept: ${instructional_design.core_concept}
- Bloom Targets: ${instructional_design.bloom_targets.join(', ')}
- Essential Question Seed: ${instructional_design.essential_question_seed}

## Sections in Plan
${plan.map((s) => `- ${s.section_id} (${s.section_type})`).join('\n')}

## Instructions

1. Derive essential_question from the essential_question_seed. Make it a clear, thought-provoking question suitable for Grade ${lesson_metadata.grade_level} ${lesson_metadata.subject} learners.

2. Create an engaging introduction_hook (1–2 sentences that draw students into the lesson).

3. Generate exactly 3 learning_targets using Bloom's taxonomy verbs from the bloom_targets list. Each target should follow the "I can [bloom_verb] [objective]" pattern. Do NOT include "I can" in the objective field — only include the verb+content after "I can".

4. Vocabulary: ${vocabInstruction}

5. ${topicDomainsInstructions}

6. lesson_id should be: "${lesson_metadata.lesson_code || `${lesson_metadata.unit_number}_${lesson_metadata.lesson_number}`}"

7. sub_competencies: copy verbatim from the curriculum data.

## Output Schema
Return ONLY valid JSON matching this exact structure:
{
  "lesson_id": "string",
  "title": "string (full lesson title)",
  "essential_question": "string (derived from seed)",
  "introduction_hook": "string (1–2 engaging sentences)",
  "learning_targets": [
    { "number": 1, "bloom_verb": "string", "objective": "string (content after I can + bloom_verb)" },
    { "number": 2, "bloom_verb": "string", "objective": "string" },
    { "number": 3, "bloom_verb": "string", "objective": "string" }
  ],
  "vocabulary": [
    { "word": "string", "definition": "string (grade-appropriate)", "example_sentence": "string" }
  ],
  "topic_domains": { "key": "topic description" },
  "core_concept": "string",
  "sub_competencies": [{ "id": "string", "label": "string" }]
}`
}
