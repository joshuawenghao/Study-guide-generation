import { callGeminiWithRetry } from './gemini'
import { MODEL_CONFIG } from './config'
import { buildSectionPlannerPrompt } from './prompts/sectionPlanner'
import { buildBlueprintPrompt } from './prompts/blueprint'
import * as introTemplate from './prompts/templates/intro'
import * as learningTargetsTemplate from './prompts/templates/learningTargets'
import * as warmupTemplate from './prompts/templates/warmup'
import * as vocabularyBoxTemplate from './prompts/templates/vocabularyBox'
import * as conceptExplainerTemplate from './prompts/templates/conceptExplainer'
import * as subconceptBlockTemplate from './prompts/templates/subconceptBlock'
import * as workedExampleTemplate from './prompts/templates/workedExample'
import * as practiceProblemsTemplate from './prompts/templates/practiceProblems'
import * as experimentDesignTemplate from './prompts/templates/experimentDesign'
import * as readingPassageTemplate from './prompts/templates/readingPassage'
import * as passageQuestionsTemplate from './prompts/templates/passageQuestions'
import * as strategyListTemplate from './prompts/templates/strategyList'
import * as deepDiveTemplate from './prompts/templates/deepDive'
import * as checkInTemplate from './prompts/templates/checkIn'
import * as keyPointsTemplate from './prompts/templates/keyPoints'
import * as assessmentPassageTemplate from './prompts/templates/assessmentPassage'
import * as assessmentQuestionsTemplate from './prompts/templates/assessmentQuestions'
import * as stepUpTemplate from './prompts/templates/stepUp'
import * as selfAssessmentTemplate from './prompts/templates/selfAssessment'
import * as answerKeyTemplate from './prompts/templates/answerKey'
import {
  validateBlueprint,
  validateSectionJSON,
  validatePlanDependencies,
  validateVocabPresence,
  validateSelfAssessTargets,
  validateAnswerKeyQuotes,
  softCheckAnswerLeakage,
} from './validators'
import type {
  Blueprint,
  GenerateRequest,
  SectionOutput,
  SectionPlan,
  SectionSpec,
  SectionType,
} from './types'

// ── Prompt template map ───────────────────────────────────────

type PromptBuilder = (
  spec: SectionSpec,
  blueprint: Blueprint,
  req: GenerateRequest,
  priorOutputs?: SectionOutput[]
) => string

const PROMPT_TEMPLATE_MAP: Record<SectionType, PromptBuilder> = {
  intro: introTemplate.buildPrompt,
  learning_targets: learningTargetsTemplate.buildPrompt,
  warmup: warmupTemplate.buildPrompt,
  vocabulary_box: vocabularyBoxTemplate.buildPrompt,
  concept_explainer: conceptExplainerTemplate.buildPrompt,
  subconcept_block: subconceptBlockTemplate.buildPrompt,
  worked_example: workedExampleTemplate.buildPrompt,
  practice_problems: practiceProblemsTemplate.buildPrompt,
  experiment_design: experimentDesignTemplate.buildPrompt,
  reading_passage: readingPassageTemplate.buildPrompt,
  passage_questions: passageQuestionsTemplate.buildPrompt,
  strategy_list: strategyListTemplate.buildPrompt,
  deep_dive: deepDiveTemplate.buildPrompt,
  check_in: checkInTemplate.buildPrompt,
  key_points: keyPointsTemplate.buildPrompt,
  assessment_passage: assessmentPassageTemplate.buildPrompt,
  assessment_questions: assessmentQuestionsTemplate.buildPrompt,
  step_up: stepUpTemplate.buildPrompt,
  self_assessment: selfAssessmentTemplate.buildPrompt,
  answer_key: answerKeyTemplate.buildPrompt,
}

// ── Wave partitioning ─────────────────────────────────────────

function partitionIntoWaves(plan: SectionPlan): SectionSpec[][] {
  const completed = new Set<string>()
  const remaining = [...plan]
  const waves: SectionSpec[][] = []

  while (remaining.length > 0) {
    const wave: SectionSpec[] = []
    const stillRemaining: SectionSpec[] = []

    for (const spec of remaining) {
      const deps = spec.depends_on ?? []
      if (deps.every((dep) => completed.has(dep))) {
        wave.push(spec)
      } else {
        stillRemaining.push(spec)
      }
    }

    if (wave.length === 0) {
      // Circular dependency or unresolvable — force all remaining into final wave
      waves.push(stillRemaining)
      break
    }

    waves.push(wave)
    for (const spec of wave) {
      completed.add(spec.section_id)
    }
    remaining.splice(0, remaining.length, ...stillRemaining)
  }

  return waves
}

// ── Temperature selector ──────────────────────────────────────

function getTemperature(sectionType: SectionType): number {
  if (sectionType === 'answer_key') return MODEL_CONFIG.answerKeyTemp
  return MODEL_CONFIG.sectionTemp
}

// ── Main pipeline ─────────────────────────────────────────────

export async function runPipeline(
  req: GenerateRequest,
  systemPrompt: string
): Promise<{
  plan: SectionPlan
  blueprint: Blueprint
  sections: SectionOutput[]
  warnings: string[]
}> {
  const warnings: string[] = []

  // ── Stage 0: Section planner ──────────────────────────────

  const plannerPrompt = buildSectionPlannerPrompt(req)
  const planRaw = await callGeminiWithRetry(
    {
      systemPrompt,
      userPrompt: plannerPrompt,
      temperature: MODEL_CONFIG.plannerTemp,
    },
    2
  )

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let plan: SectionPlan
  try {
    plan = JSON.parse(planRaw) as SectionPlan
  } catch {
    throw new Error(`Section planner returned invalid JSON: ${planRaw.slice(0, 200)}`)
  }

  // Validate plan
  const seenIds = new Set<string>()
  for (const spec of plan) {
    if (seenIds.has(spec.section_id)) {
      throw new Error(`Duplicate section_id in plan: "${spec.section_id}"`)
    }
    seenIds.add(spec.section_id)
  }
  validatePlanDependencies(plan)

  // ── Stage 1: Blueprint ────────────────────────────────────

  const blueprintPrompt = buildBlueprintPrompt(req, plan)
  const blueprintRaw = await callGeminiWithRetry(
    {
      systemPrompt,
      userPrompt: blueprintPrompt,
      temperature: MODEL_CONFIG.blueprintTemp,
    },
    2
  )

  let blueprint: Blueprint
  try {
    blueprint = JSON.parse(blueprintRaw) as Blueprint
  } catch {
    throw new Error(`Blueprint generator returned invalid JSON: ${blueprintRaw.slice(0, 200)}`)
  }

  validateBlueprint(blueprint)

  // ── Stage 2: Section generation ───────────────────────────

  const waves = partitionIntoWaves(plan)
  const completedSections: SectionOutput[] = []

  for (const wave of waves) {
    const waveResults = await Promise.all(
      wave.map(async (spec): Promise<SectionOutput> => {
        // Collect prior outputs this section depends on
        const priorOutputs = completedSections.filter((s) =>
          (spec.depends_on ?? []).includes(s.section_id)
        )

        const templateFn = PROMPT_TEMPLATE_MAP[spec.section_type]
        if (!templateFn) {
          throw new Error(`No prompt template found for section_type: "${spec.section_type}"`)
        }

        const userPrompt = templateFn(spec, blueprint, req, priorOutputs)
        const temperature = getTemperature(spec.section_type)

        const raw = await callGeminiWithRetry(
          {
            systemPrompt,
            userPrompt,
            temperature,
          },
          2
        )

        const content = validateSectionJSON(spec.section_id, raw)

        return {
          section_id: spec.section_id,
          section_type: spec.section_type,
          order: spec.order,
          content,
          raw,
        }
      })
    )

    completedSections.push(...waveResults)
  }

  // Sort by order for final output
  completedSections.sort((a, b) => a.order - b.order)

  // ── Stage 3: Validate ─────────────────────────────────────

  // Vocab presence check
  const missingVocab = validateVocabPresence(blueprint, completedSections)
  if (missingVocab.length > 0) {
    warnings.push(`Missing vocabulary words in vocabulary_box: ${missingVocab.join(', ')}`)
  }

  // Self-assessment targets check
  const selfAssessOutput = completedSections.find((s) => s.section_type === 'self_assessment')
  if (selfAssessOutput) {
    const selfAssessValid = validateSelfAssessTargets(blueprint, selfAssessOutput)
    if (!selfAssessValid) {
      warnings.push('Self-assessment skills do not fully match blueprint learning targets')
    }
  }

  // Answer key quote validation
  const answerKeyOutput = completedSections.find((s) => s.section_type === 'answer_key')
  if (answerKeyOutput) {
    const quotesValid = validateAnswerKeyQuotes(completedSections, answerKeyOutput)
    if (!quotesValid) {
      warnings.push('Answer key contains quoted text not found verbatim in source passages')
    }

    // Soft: answer leakage check
    const leakageResult = softCheckAnswerLeakage(completedSections, answerKeyOutput)
    if (!leakageResult.passed) {
      warnings.push(...leakageResult.warnings)
    }
  }

  return { plan, blueprint, sections: completedSections, warnings }
}
