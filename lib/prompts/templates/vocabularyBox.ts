import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  return `Generate the vocabulary box section for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}
- Vocabulary from Blueprint:
${blueprint.vocabulary.map((v) => `  - ${v.word}: ${v.definition} (Example: ${v.example_sentence})`).join('\n')}

## Instructions
For each vocabulary word in the blueprint, generate a complete vocabulary entry with:
- word: exactly as given in the blueprint
- part_of_speech: the grammatical role (noun, verb, adjective, etc.)
- definition: grade-appropriate definition suitable for Grade ${lesson_metadata.grade_level}
- example_sentence: a clear, concrete sentence using the word in context relevant to ${lesson_metadata.market} learners

Use ALL ${blueprint.vocabulary.length} vocabulary words from the blueprint. Do not add or remove any.

## Output Schema
{
  "vocabulary_box": [
    {
      "word": "string",
      "part_of_speech": "string",
      "definition": "string (grade-appropriate)",
      "example_sentence": "string"
    }
  ]
}

Section spec: ${JSON.stringify(spec)}`
}
