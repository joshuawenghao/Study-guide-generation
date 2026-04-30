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

  return `Generate a check-in question for this reading passage.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Essential Question: ${blueprint.essential_question}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}

## Reading Passage: "${passageTitle}"
${passageBody}

## Instructions
Create ONE open-ended check-in question that:
1. Requires students to find and use evidence from the passage above
2. Connects back to the essential question: "${blueprint.essential_question}"
3. Is thought-provoking but answerable by a Grade ${lesson_metadata.grade_level} student
4. Ends with a directive to use evidence (e.g. "Use evidence from the text to support your answer.")

Also provide a sentence starter that helps students begin their response.

## Output Schema
{
  "question": "string (open-ended, requires evidence from the passage)",
  "sentence_starter": "string (e.g. 'Based on the passage, I think... because...')"
}

Section spec: ${JSON.stringify(spec)}`
}
