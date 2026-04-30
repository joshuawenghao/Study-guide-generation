import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  return `Design an experiment for this science study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}
- Topic Domains: ${JSON.stringify(blueprint.topic_domains)}

## Instructions
Design a safe, classroom-appropriate experiment that:
1. Investigates an aspect of the core concept: "${blueprint.core_concept}"
2. Uses materials that are readily available in ${lesson_metadata.market} schools
3. Has clear, numbered procedure steps (4–6 steps)
4. Includes an observation table with appropriate columns for recording data
5. Has 3 analysis questions that guide students to connect observations to the concept
6. Is appropriate for Grade ${lesson_metadata.grade_level} safety and skill level

## Output Schema
{
  "experiment_title": "string",
  "objective": "string (what students will investigate and learn)",
  "materials": ["string"],
  "procedure": [{ "step": 1, "instruction": "string" }],
  "observations_table": {
    "columns": ["string (column headers)"],
    "rows": 3
  },
  "analysis_questions": ["string"]
}

Section spec: ${JSON.stringify(spec)}`
}
