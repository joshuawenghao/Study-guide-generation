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
  const assessmentQuestionsOutput = priorOutputs?.find(
    (o) => o.section_type === 'assessment_questions'
  )

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const passageContent = assessmentPassageOutput?.content as any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const questionsContent = assessmentQuestionsOutput?.content as any

  const passageTitle: string = passageContent?.passage_title ?? 'Assessment Passage'
  const questionsList: string = questionsContent?.questions
    ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
      questionsContent.questions.map((q: any) => `${q.number}. ${q.question}`).join('\n')
    : '[Assessment questions not yet generated]'

  return `Generate a step-up writing prompt for the assessment section.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Essential Question: ${blueprint.essential_question}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}

## Assessment Passage: "${passageTitle}"
## Assessment Questions Already Given:
${questionsList}

## Instructions
Write a step-up writing prompt (2–3 sentences) that:
1. Goes beyond the comprehension questions — it asks students to synthesise, evaluate, or create
2. Requires students to use evidence from the passage
3. Ends with a clear directive to use textual evidence (e.g. "Use specific details from the text to support your response.")
4. Is ambitious but achievable for Grade ${lesson_metadata.grade_level}

## Output Schema
{
  "prompt": "string (2–3 sentences, ends with directive to use evidence)"
}

Section spec: ${JSON.stringify(spec)}`
}
