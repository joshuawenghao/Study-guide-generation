import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  return `Create a warm-up activity for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Essential Question: ${blueprint.essential_question}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}

## Instructions
Design a short warm-up activity (5–10 minutes) that:
1. Activates prior knowledge relevant to this lesson
2. Is appropriate for Grade ${lesson_metadata.grade_level} ${lesson_metadata.subject}
3. Connects to the core concept: ${blueprint.core_concept}
4. Uses concrete, locally relevant examples for ${lesson_metadata.market} learners
5. Instructions should be numbered steps (2–3 steps)

## Output Schema
{
  "activity_title": "string (short, descriptive title)",
  "instructions": "string (2–3 numbered steps, e.g. '1. ... 2. ... 3. ...')",
  "purpose": "string (1 sentence explaining what prior skill or knowledge this activates)"
}

Section spec: ${JSON.stringify(spec)}`
}
