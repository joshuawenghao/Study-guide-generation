import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  const subconceptIndex =
    typeof spec.config?.subconcept_index === 'number' ? spec.config.subconcept_index : 0
  const subCompetency = blueprint.sub_competencies[subconceptIndex]

  return `Write a subconcept block for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}

## Target Sub-competency (index ${subconceptIndex})
- ID: ${subCompetency?.id ?? 'N/A'}
- Label: ${subCompetency?.label ?? 'N/A'}

## All Sub-competencies for Context
${blueprint.sub_competencies.map((sc, i) => `  ${i}. ${sc.id}: ${sc.label}`).join('\n')}

## Topic Domains
${JSON.stringify(blueprint.topic_domains, null, 2)}

## Instructions
Write a detailed block for the sub-competency "${subCompetency?.label ?? 'N/A'}". Include:
1. A clear subconcept title derived from the sub-competency label
2. A thorough explanation (3–4 sentences) of this specific sub-competency
3. An example_text: a short paragraph using context from the topic domains that illustrates the sub-competency in action
4. An analysis: 2–3 sentences that discuss or analyse the example

Language: Grade ${lesson_metadata.grade_level} level. Market: ${lesson_metadata.market}.

## Output Schema
{
  "subconcept_id": "string (the sub-competency id)",
  "subconcept_title": "string",
  "explanation": "string (3–4 sentences)",
  "example_text": "string (short paragraph using relevant topic domain content)",
  "analysis": "string (2–3 sentences)"
}

Section spec: ${JSON.stringify(spec)}`
}
