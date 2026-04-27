import type { Blueprint, GenerateRequest, SectionOutput, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest,
  priorOutputs?: SectionOutput[]
): string {
  const { lesson_metadata } = req

  const assessmentPassageOutput = priorOutputs?.find(
    (o) => o.section_type === 'assessment_passage'
  )
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const passageContent = assessmentPassageOutput?.content as any
  const passageBody: string = passageContent?.passage_body ?? '[Assessment passage not yet generated]'
  const passageTitle: string = passageContent?.passage_title ?? 'Assessment Passage'

  return `Generate assessment questions for the assessment passage below.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Learning Targets:
${blueprint.learning_targets.map((lt) => `  ${lt.number}. I can ${lt.bloom_verb} ${lt.objective}`).join('\n')}

## Assessment Passage: "${passageTitle}"
${passageBody}

## Instructions
Generate exactly 5 open-ended assessment questions that:
1. Question 1–3: Test comprehension and understanding of the passage
2. Question 4: Asks students to analyse the tone, mood, or author's purpose
3. Question 5: Requires inference or transfer — students apply what they learned to a new situation or make a connection beyond the text
4. All questions require evidence from the passage
5. Questions progress from lower- to higher-order thinking
6. Appropriate for Grade ${lesson_metadata.grade_level}

## Output Schema
{
  "questions": [
    { "number": 1, "question": "string", "type": "open_ended" },
    { "number": 2, "question": "string", "type": "open_ended" },
    { "number": 3, "question": "string", "type": "open_ended" },
    { "number": 4, "question": "string (tone analysis)", "type": "open_ended" },
    { "number": 5, "question": "string (inference/transfer)", "type": "open_ended" }
  ]
}

Section spec: ${JSON.stringify(spec)}`
}
