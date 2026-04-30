import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata, curriculum } = req
  return `Generate the learning targets section for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Competency: ${curriculum.competency_code} — ${curriculum.competency_description}
- Learning Targets from Blueprint:
${blueprint.learning_targets.map((lt) => `  ${lt.number}. [${lt.bloom_verb}] ${lt.objective}`).join('\n')}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}

## Instructions
Generate the learning competency statement and the 3 learning targets using "I can..." format.
Each statement should use the bloom_verb from the blueprint and express what a student will be able to do.
Keep language simple and appropriate for Grade ${lesson_metadata.grade_level}.

## Output Schema
{
  "learning_competency": "string (the overall competency in student-friendly language)",
  "learning_targets": [
    { "number": 1, "statement": "string (I can... format)" },
    { "number": 2, "statement": "string (I can... format)" },
    { "number": 3, "statement": "string (I can... format)" }
  ]
}

Section spec: ${JSON.stringify(spec)}`
}
