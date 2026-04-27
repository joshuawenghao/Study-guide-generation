import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  const assessmentPassageTopic =
    blueprint.topic_domains['assessment_passage'] ??
    `a different aspect of ${blueprint.core_concept}`

  return `Write an assessment reading passage for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}
- Topic for this assessment passage: ${assessmentPassageTopic}

## Instructions
Write a 4–6 paragraph assessment passage (approximately 350 words) that:
1. Uses the topic: "${assessmentPassageTopic}"
2. Is DIFFERENT from any model reading passage in the lesson — students encounter this text fresh
3. Is written at Flesch-Kincaid grade ${lesson_metadata.grade_level} reading level
4. Has an engaging title
5. Is culturally appropriate for ${lesson_metadata.market} learners
6. Contains details that students can cite as evidence in their answers
7. Sets a clear purpose_label: "entertain", "inform", or "persuade"

IMPORTANT: This passage must be entirely different from any earlier reading passage in the lesson.

## Output Schema
{
  "passage_title": "string",
  "passage_body": "string (4–6 paragraphs separated by \\n\\n, approximately 350 words, topic: ${assessmentPassageTopic})",
  "purpose_label": "string (entertain | inform | persuade)"
}

Section spec: ${JSON.stringify(spec)}`
}
