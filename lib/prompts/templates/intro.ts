import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  return `Write an engaging introduction for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Essential Question: ${blueprint.essential_question}
- Introduction Hook: ${blueprint.introduction_hook}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}

## Instructions
Write 2–3 paragraphs that:
1. Open warmly and reference the essential question to engage students
2. Briefly explain what students will learn in this lesson
3. Connect the topic to real-world relevance for Grade ${lesson_metadata.grade_level} learners in ${lesson_metadata.market}

The tone should be warm, clear, and encouraging. Never condescending. No exclamation marks.

## Output Schema
{
  "introduction": "string (2–3 paragraphs separated by \\n\\n)"
}

Section spec: ${JSON.stringify(spec)}`
}
