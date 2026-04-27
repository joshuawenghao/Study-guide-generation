import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  return `Write a deep dive section for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Essential Question: ${blueprint.essential_question}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}
- Topic Domains: ${JSON.stringify(blueprint.topic_domains)}
- Sub-competencies: ${blueprint.sub_competencies.map((sc) => `${sc.id}: ${sc.label}`).join('; ')}

## Instructions
Write a deep dive section (4–5 paragraphs) that:
1. Explores the core concept in greater depth
2. Goes beyond basic definitions to examine nuances, implications, or applications
3. Connects to the essential question: "${blueprint.essential_question}"
4. Uses concrete examples and evidence appropriate for Grade ${lesson_metadata.grade_level}
5. Builds critical thinking by presenting multiple perspectives or dimensions of the concept
6. Is culturally appropriate for ${lesson_metadata.market} learners

## Output Schema
{
  "section_title": "string",
  "body": "string (4–5 paragraphs separated by \\n\\n)"
}

Section spec: ${JSON.stringify(spec)}`
}
