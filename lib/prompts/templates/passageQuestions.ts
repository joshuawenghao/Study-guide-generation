import type { Blueprint, GenerateRequest, SectionOutput, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest,
  priorOutputs?: SectionOutput[]
): string {
  const { lesson_metadata } = req

  const readingPassageOutput = priorOutputs?.find(
    (o) => o.section_type === 'reading_passage'
  )
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const passageContent = readingPassageOutput?.content as any
  const passageBody: string = passageContent?.passage_body ?? '[Reading passage not yet generated]'
  const passageTitle: string = passageContent?.passage_title ?? 'Reading Passage'

  return `Generate comprehension questions for the reading passage below.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Learning Targets:
${blueprint.learning_targets.map((lt) => `  ${lt.number}. I can ${lt.bloom_verb} ${lt.objective}`).join('\n')}

## Reading Passage: "${passageTitle}"
${passageBody}

## Instructions
Generate 4–5 open-ended comprehension questions about the passage above that:
1. Require students to demonstrate understanding of the text
2. Progress from literal comprehension to inferential thinking
3. Connect to the lesson's learning targets
4. Are appropriate for Grade ${lesson_metadata.grade_level}
5. Require students to reference or cite evidence from the passage

## Output Schema
{
  "questions": [
    { "number": 1, "question": "string", "type": "open_ended" }
  ]
}

Section spec: ${JSON.stringify(spec)}`
}
