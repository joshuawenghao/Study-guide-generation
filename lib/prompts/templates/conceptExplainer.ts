import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata, curriculum } = req
  return `Write the concept explainer section for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Essential Question: ${blueprint.essential_question}
- Competency: ${curriculum.competency_description}
- Sub-competencies: ${blueprint.sub_competencies.map((sc) => `${sc.id}: ${sc.label}`).join('; ')}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}

## Instructions
Write a concept explainer that:
1. Has a clear, descriptive section title
2. Opens with a paragraph that situates the concept in the students' world
3. Gives a concise 2–3 sentence concept overview that defines and explains the core concept
4. Uses concrete examples appropriate for Grade ${lesson_metadata.grade_level} ${lesson_metadata.market} learners
5. Language must be at Flesch-Kincaid grade ${lesson_metadata.grade_level} level

## Output Schema
{
  "section_title": "string",
  "opening_paragraph": "string (1 paragraph situating the concept)",
  "concept_overview": "string (2–3 sentences defining and explaining the core concept)"
}

Section spec: ${JSON.stringify(spec)}`
}
