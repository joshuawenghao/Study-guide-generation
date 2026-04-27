import type { Blueprint, GenerateRequest, SectionOutput, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest,
  priorOutputs?: SectionOutput[]
): string {
  const { lesson_metadata } = req

  // Collect all answerable sections (questions and problems)
  const answerableSections = (priorOutputs ?? []).filter((o) =>
    [
      'practice_problems',
      'passage_questions',
      'assessment_questions',
      'check_in',
      'experiment_design',
    ].includes(o.section_type)
  )

  const sectionSummaries = answerableSections
    .map((s) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const content = s.content as any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const questions: Array<{ number?: number; question?: string }> =
        content?.questions ??
        content?.problems ??
        (Array.isArray(content?.analysis_questions)
          ? content.analysis_questions.map((q: string, i: number) => ({ number: i + 1, question: q }))
          : undefined) ??
        (content?.question ? [{ number: 1, question: content.question }] : [])
      return `Section: ${s.section_id} (${s.section_type})\nQuestions:\n${
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        Array.isArray(questions) ? questions.map((q: any) => `  ${q.number ?? ''}: ${q.question ?? q}`).join('\n') : JSON.stringify(questions)
      }`
    })
    .join('\n\n')

  // Get passage content for quote validation
  const passageSections = (priorOutputs ?? []).filter(
    (o) => o.section_type === 'reading_passage' || o.section_type === 'assessment_passage'
  )
  const passageContext = passageSections
    .map((s) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const content = s.content as any
      return `Passage "${content?.passage_title ?? s.section_id}":\n${content?.passage_body ?? ''}`
    })
    .join('\n\n')

  return `Generate the answer key for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}

## Source Passages (use these for evidence-based answers)
${passageContext || 'No passages in this lesson.'}

## Questions to Answer
${sectionSummaries || 'No answerable sections found.'}

## Instructions
Generate model answers for each question above. For each answer:
1. Echo the question text in the "question" field
2. Provide a complete, well-reasoned possible answer appropriate for Grade ${lesson_metadata.grade_level}
3. For reading/assessment passage questions: quote directly from the relevant passage to support the answer (use quotation marks around verbatim quotes)
4. For math/science problems: show the key steps and the final answer
5. Answers should be exemplary but accessible — a model of what a good student response looks like

## Output Schema
{
  "answers": [
    {
      "section_id": "string (the section_id this question belongs to)",
      "question": "string (echoed from the question)",
      "possible_answer": "string (must quote from source passage where applicable)"
    }
  ]
}

Section spec: ${JSON.stringify(spec)}`
}
