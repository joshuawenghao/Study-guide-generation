import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  return `Generate a list of reading strategies for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}

## Instructions
Generate 4–5 reading comprehension strategies relevant to ${lesson_metadata.subject} for Grade ${lesson_metadata.grade_level}. For each strategy:
1. Give it a clear, memorable name
2. Write a 1–2 sentence description of what the strategy involves and when to use it
3. List 3–5 signal words or phrases that indicate when this strategy is helpful

Strategies should be practical and appropriate for ${lesson_metadata.grade_level} students.

## Output Schema
{
  "strategies": [
    {
      "name": "string",
      "description": "string (1–2 sentences)",
      "signal_words": ["string"]
    }
  ]
}

Section spec: ${JSON.stringify(spec)}`
}
