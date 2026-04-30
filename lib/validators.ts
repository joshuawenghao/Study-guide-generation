import type { Blueprint, SectionOutput, SectionPlan } from './types'

// Hard: throws if blueprint missing required fields
export function validateBlueprint(blueprint: Blueprint): void {
  if (!blueprint.lesson_id) throw new Error('Blueprint missing lesson_id')
  if (!blueprint.title) throw new Error('Blueprint missing title')
  if (!blueprint.essential_question) throw new Error('Blueprint missing essential_question')
  if (!blueprint.introduction_hook) throw new Error('Blueprint missing introduction_hook')
  if (!Array.isArray(blueprint.learning_targets) || blueprint.learning_targets.length === 0) {
    throw new Error('Blueprint missing learning_targets')
  }
  if (!Array.isArray(blueprint.vocabulary) || blueprint.vocabulary.length === 0) {
    throw new Error('Blueprint missing vocabulary')
  }
  if (!blueprint.core_concept) throw new Error('Blueprint missing core_concept')
  if (!Array.isArray(blueprint.sub_competencies)) {
    throw new Error('Blueprint missing sub_competencies')
  }
}

// Hard: throws if raw string is not valid JSON
export function validateSectionJSON(sectionId: string, raw: string): unknown {
  try {
    return JSON.parse(raw)
  } catch (err) {
    throw new Error(
      `Section "${sectionId}" returned invalid JSON: ${err instanceof Error ? err.message : String(err)}`
    )
  }
}

// Hard: returns missing vocabulary words (empty array = pass)
export function validateVocabPresence(
  blueprint: Blueprint,
  sections: SectionOutput[]
): string[] {
  const vocabSection = sections.find((s) => s.section_type === 'vocabulary_box')
  if (!vocabSection) return []

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const content = vocabSection.content as any
  if (!content?.vocabulary_box || !Array.isArray(content.vocabulary_box)) return []

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const generatedWords = new Set(content.vocabulary_box.map((v: any) => v.word?.toLowerCase()))
  const missing: string[] = []
  for (const vocabItem of blueprint.vocabulary) {
    if (!generatedWords.has(vocabItem.word?.toLowerCase())) {
      missing.push(vocabItem.word)
    }
  }
  return missing
}

// Hard: returns true if self_assessment skills match blueprint learning targets
export function validateSelfAssessTargets(
  blueprint: Blueprint,
  selfAssessOutput: SectionOutput
): boolean {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const content = selfAssessOutput.content as any
  if (!content?.self_assessment?.rows || !Array.isArray(content.self_assessment.rows)) {
    return false
  }

  const blueprintObjectives = new Set(
    blueprint.learning_targets.map((lt) => lt.objective.toLowerCase().trim())
  )

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  for (const row of content.self_assessment.rows) {
    if (!blueprintObjectives.has(row.skill?.toLowerCase().trim())) {
      return false
    }
  }
  return true
}

// Hard: returns true if answer key quotes exist verbatim in source passages
export function validateAnswerKeyQuotes(
  sections: SectionOutput[],
  answerKeyOutput: SectionOutput
): boolean {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const content = answerKeyOutput.content as any
  if (!content?.answers || !Array.isArray(content.answers)) return true

  const passageSections = sections.filter(
    (s) => s.section_type === 'reading_passage' || s.section_type === 'assessment_passage'
  )

  const allPassageText = passageSections
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    .map((s) => (s.content as any)?.passage_body ?? '')
    .join(' ')
    .toLowerCase()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  for (const answer of content.answers) {
    const possibleAnswer: string = answer.possible_answer ?? ''
    // Check if the answer contains a quoted phrase (text in quotes)
    const quoteMatches = possibleAnswer.match(/"([^"]+)"/g)
    if (quoteMatches) {
      for (const quote of quoteMatches) {
        const quoteText = quote.replace(/"/g, '').toLowerCase()
        // Only validate non-trivial quotes (> 10 chars)
        if (quoteText.length > 10 && !allPassageText.includes(quoteText)) {
          return false
        }
      }
    }
  }
  return true
}

// Soft: checks for answer leakage between body and answer key
export function softCheckAnswerLeakage(
  sections: SectionOutput[],
  answerKeyOutput: SectionOutput
): { passed: boolean; warnings: string[] } {
  const warnings: string[] = []

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const answerContent = answerKeyOutput.content as any
  if (!answerContent?.answers || !Array.isArray(answerContent.answers)) {
    return { passed: true, warnings }
  }

  const practiceSections = sections.filter(
    (s) =>
      s.section_type === 'practice_problems' ||
      s.section_type === 'passage_questions' ||
      s.section_type === 'assessment_questions'
  )

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  for (const answer of answerContent.answers) {
    const possibleAnswer: string = (answer.possible_answer ?? '').toLowerCase()
    for (const section of practiceSections) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const sectionContent = section.content as any
      const questions =
        sectionContent?.questions ?? sectionContent?.problems ?? []
      if (Array.isArray(questions)) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        for (const q of questions) {
          const questionText: string = (q.question ?? '').toLowerCase()
          if (
            questionText.length > 20 &&
            possibleAnswer.length > 20 &&
            questionText.includes(possibleAnswer.slice(0, 30))
          ) {
            warnings.push(
              `Possible answer leakage detected in section "${section.section_id}" for answer_key entry "${answer.section_id}"`
            )
          }
        }
      }
    }
  }

  return { passed: warnings.length === 0, warnings }
}

// Hard: checks all depends_on references resolve to real section_ids in the plan
export function validatePlanDependencies(plan: SectionPlan): void {
  const ids = new Set(plan.map((s) => s.section_id))
  for (const spec of plan) {
    if (spec.depends_on) {
      for (const dep of spec.depends_on) {
        if (!ids.has(dep)) {
          throw new Error(
            `Section "${spec.section_id}" depends_on unknown section_id "${dep}"`
          )
        }
      }
    }
  }
}
