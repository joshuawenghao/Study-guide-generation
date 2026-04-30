import type { Blueprint, GenerateRequest, SectionSpec } from '../../types'

export function buildPrompt(
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest
): string {
  const { lesson_metadata } = req
  const difficulty = (spec.config?.difficulty as string) ?? 'basic'
  const exampleNumber = (spec.config?.example_number as number) ?? 1

  return `Generate a worked example for this study guide.

## Blueprint Context
- Lesson Title: ${blueprint.title}
- Core Concept: ${blueprint.core_concept}
- Subject: ${lesson_metadata.subject}
- Grade Level: ${lesson_metadata.grade_level}
- Market: ${lesson_metadata.market}
- Topic Domains: ${JSON.stringify(blueprint.topic_domains)}

## This Example
- Example Number: ${exampleNumber}
- Difficulty: ${difficulty}
- Context: Use the topic domain context relevant to ${lesson_metadata.subject}

## Instructions
Create a complete worked example at "${difficulty}" difficulty level. The example should:
1. Have a clear, descriptive title indicating the type of problem
2. Present a realistic problem statement appropriate for Grade ${lesson_metadata.grade_level} ${lesson_metadata.subject}
3. Solve the problem step by step — each step must have an action and an explanation of WHY that step is taken
4. Provide a clear final answer
5. Use plain text for all math (no LaTeX). Use Unicode symbols where needed (e.g. ×, ÷, ², √).
6. Make examples culturally relevant to ${lesson_metadata.market}

Difficulty guidelines:
- basic: single-step or two-step problem, familiar context
- intermediate: multi-step problem, moderate complexity
- advanced: complex problem, may require applying multiple concepts

## Output Schema
{
  "example_title": "string",
  "problem_statement": "string",
  "solution_steps": [
    { "step": 1, "action": "string", "explanation": "string" }
  ],
  "answer": "string"
}

Section spec: ${JSON.stringify(spec)}`
}
