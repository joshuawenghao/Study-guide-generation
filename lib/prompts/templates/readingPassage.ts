import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  const modelPassageTopic =
    blueprint.topic_domains['model_passage'] ?? blueprint.core_concept

  return `Write a reading passage for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Essential Question: ${blueprint.essential_question}
- Topic for this passage: ${modelPassageTopic}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}

## Instructions
Write a 4–6 paragraph reading passage (approximately 350 words) that:
1. Uses the topic: "${modelPassageTopic}"
2. Is written at Flesch-Kincaid grade ${lesson_metadata.grade_level} reading level
3. Serves as a model text for the lesson — students will answer comprehension questions about it
4. Has an engaging title that reflects the content
5. Demonstrates good paragraph structure with clear topic sentences
6. Is culturally appropriate and relevant for ${lesson_metadata.market} learners
7. Sets a purpose_label: "entertain", "inform", or "persuade" based on the text type chosen

## Output Schema
{
  "passage_title": "string",
  "passage_body": "string (4–6 paragraphs separated by \\n\\n, approximately 350 words, topic: ${modelPassageTopic})",
  "purpose_label": "string (entertain | inform | persuade)"
}

Section spec: ${JSON.stringify(spec)}`
}
