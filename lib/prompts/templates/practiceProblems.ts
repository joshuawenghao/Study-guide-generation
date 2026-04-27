import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  const count = typeof spec.config?.count === 'number' ? spec.config.count : 5

  return `Generate practice problems for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}
- Learning Targets:
${blueprint.learning_targets.map((lt) => `  ${lt.number}. I can ${lt.bloom_verb} ${lt.objective}`).join('\n')}

## Instructions
Generate exactly ${count} practice problems that:
1. Cover the learning targets for this lesson
2. Vary in question type (mix of short_answer, multiple_choice, and open_ended)
3. Progress from simpler to more complex
4. Use concrete, familiar contexts for Grade ${lesson_metadata.grade_level} ${lesson_metadata.subject} learners in ${lesson_metadata.market}
5. For multiple_choice questions, include the 4 options in the question text itself (A, B, C, D format)
6. Use plain text for all math (no LaTeX)

## Output Schema
{
  "problems": [
    {
      "number": 1,
      "question": "string",
      "type": "short_answer | multiple_choice | open_ended"
    }
  ]
}

Generate exactly ${count} problems. Section spec: ${JSON.stringify(spec)}`
}
