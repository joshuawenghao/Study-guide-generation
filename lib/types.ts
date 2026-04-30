// ── Input types ──────────────────────────────────────────────

export interface LessonMetadata {
  subject: string           // e.g. "English", "Mathematics", "Science"
  grade_level: number       // 1–12
  market: string            // e.g. "PH", "JP", "VN"
  language: string          // e.g. "en", "ja", "vi"
  unit_number: number
  unit_title: string
  lesson_number: number
  lesson_title: string
  lesson_code: string
}

export interface SubCompetency {
  id: string
  label: string
}

export interface Curriculum {
  competency_code: string
  competency_description: string
  sub_competencies: SubCompetency[]
}

export interface InstructionalDesign {
  core_concept: string
  bloom_targets: [string, string, string]
  essential_question_seed: string
}

export interface OptionalInputs {
  vocabulary_seeds?: string[]
  topic_domains?: Record<string, string>
  tone_register?: string
  length_preset?: 'standard' | 'short' | 'long'
}

export interface GenerateRequest {
  lesson_metadata: LessonMetadata
  curriculum: Curriculum
  instructional_design: InstructionalDesign
  optional?: OptionalInputs
}

// ── Section plan types (Stage 0 output) ──────────────────────

export type SectionType =
  | 'intro'
  | 'learning_targets'
  | 'warmup'
  | 'vocabulary_box'
  | 'concept_explainer'
  | 'subconcept_block'
  | 'worked_example'
  | 'practice_problems'
  | 'experiment_design'
  | 'reading_passage'
  | 'passage_questions'
  | 'strategy_list'
  | 'deep_dive'
  | 'check_in'
  | 'key_points'
  | 'assessment_passage'
  | 'assessment_questions'
  | 'step_up'
  | 'self_assessment'
  | 'answer_key'

export interface SectionSpec {
  section_id: string         // unique slug, e.g. "worked_example_1"
  section_type: SectionType  // maps to a prompt template file
  order: number              // render order in final doc
  depends_on?: string[]      // section_ids that must complete first
  config?: Record<string, unknown>  // section-specific params e.g. { difficulty: "basic", count: 5 }
}

export type SectionPlan = SectionSpec[]

// ── Blueprint type (Stage 1 output) ──────────────────────────

export interface Blueprint {
  lesson_id: string
  title: string
  essential_question: string
  introduction_hook: string
  learning_targets: Array<{
    number: number
    bloom_verb: string
    objective: string
  }>
  vocabulary: Array<{
    word: string
    definition: string
    example_sentence: string
  }>
  topic_domains: Record<string, string>
  core_concept: string
  sub_competencies: SubCompetency[]
}

// ── Section output types ──────────────────────────────────────

export interface SectionOutput {
  section_id: string
  section_type: SectionType
  order: number
  content: unknown   // parsed JSON, shape varies by section_type
  raw: string        // raw Gemini response string (for debugging)
}

// ── Final response type ───────────────────────────────────────

export interface GenerateResponse {
  success: boolean
  plan?: SectionPlan
  blueprint?: Blueprint
  sections?: SectionOutput[]
  docxBase64?: string
  warnings?: string[]
  error?: string
}

// ── Progress stage type ───────────────────────────────────────

export type ProgressStage =
  | 'idle'
  | 'planning'
  | 'blueprint'
  | 'sections'
  | 'validating'
  | 'rendering'
  | 'done'
  | 'error'
