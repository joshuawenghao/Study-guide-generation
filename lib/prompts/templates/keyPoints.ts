import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  return `Generate the key points summary for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Learning Targets:
${blueprint.learning_targets.map((lt) => `  ${lt.number}. I can ${lt.bloom_verb} ${lt.objective}`).join('\n')}
- Sub-competencies: ${blueprint.sub_competencies.map((sc) => `${sc.label}`).join('; ')}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}

## Instructions
Write exactly 3 key point statements that:
1. Summarise the most important takeaways from this lesson
2. Correspond directly to the 3 learning targets
3. Are concise, clear statements (1 sentence each) that a student could use for review
4. Use bold-worthy language that stands out in the document
5. Are appropriate for Grade ${lesson_metadata.grade_level}

## Output Schema
{
  "key_points": [
    { "number": 1, "statement": "string" },
    { "number": 2, "statement": "string" },
    { "number": 3, "statement": "string" }
  ]
}

Section spec: ${JSON.stringify(spec)}`
}
