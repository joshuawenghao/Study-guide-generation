import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  return `Generate the self-assessment section for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Learning Targets (use these VERBATIM as skill statements):
${blueprint.learning_targets.map((lt) => `  ${lt.number}. ${lt.objective}`).join('\n')}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}

## Instructions
Create a self-assessment table where:
1. Each row corresponds to one learning target from the blueprint
2. The "skill" field must be VERBATIM from blueprint.learning_targets[].objective
3. Each row has columns: needs_assistance, minimal_understanding, confident (these are checkbox columns — do not add descriptive text, just the column name)
4. Include exactly ${blueprint.learning_targets.length} rows, one per learning target

Also include the 4 reflection stems EXACTLY as specified below — do not change any word.

## Output Schema
{
  "self_assessment": {
    "rows": [
      {
        "skill": "string (verbatim from blueprint learning_targets[].objective)",
        "columns": ["needs_assistance", "minimal_understanding", "confident"]
      }
    ]
  },
  "reflection_stems": [
    "I find _____ the most interesting because _____.",
    "I need to improve on _____ because _____.",
    "I need to practice _____ because _____.",
    "I plan to _____."
  ]
}

Section spec: ${JSON.stringify(spec)}`
}
