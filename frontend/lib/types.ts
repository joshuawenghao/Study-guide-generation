// Mirrors backend/types.py. When changing fields in either file, update both in the same commit.

export type LengthPreset = "short" | "standard" | "long";

export interface TopicDomains {
  model_passage: string;
  assessment_passage: string;
  entertain_example: string;
  inform_example: string;
  persuade_example: string;
}

export interface SubCompetency {
  id: string;
  label: string;
}

export interface LessonMetadata {
  subject: string;
  grade_level: number;
  market: string;
  language: string;
  unit_number: number;
  unit_title: string;
  lesson_number: number;
  lesson_title: string;
  lesson_code: string;
}

export interface Curriculum {
  competency_code: string;
  competency_description: string;
  sub_competencies: SubCompetency[];
}

export interface InstructionalDesign {
  core_concept: string;
  bloom_targets: [string, string, string];
  essential_question_seed: string;
}

export interface OptionalInputs {
  vocabulary_seeds: string[] | undefined;
  topic_domains: Record<string, string> | undefined;
  tone_register: string;
  length_preset: LengthPreset;
}

export interface GenerateRequest {
  lesson_metadata: LessonMetadata;
  curriculum: Curriculum;
  instructional_design: InstructionalDesign;
  optional: OptionalInputs;
}

export interface LearningTarget {
  number: number;
  bloom_verb: string;
  objective: string;
}

export interface VocabEntry {
  word: string;
  definition: string;
  example_sentence: string;
}

export interface Blueprint {
  lesson_id: string;
  title: string;
  essential_question: string;
  introduction_hook: string;
  learning_targets: LearningTarget[];
  vocabulary: VocabEntry[];
  topic_domains: TopicDomains;
  sub_competencies: SubCompetency[];
  core_concept: string;
}

export interface PreviewSection {
  section_id: string;
  section_type: string;
  title: string;
  content: Record<string, unknown>;
}

export interface WebPreviewPayload {
  sections: PreviewSection[];
}

export interface ValidationResult {
  passed: boolean;
  failed_sections: string[];
  failures: Record<string, string[]>;
  warnings: string[];
  best_effort_sections: string[];
}

export interface GenerateResponse {
  success: boolean;
  pdf_base64: string;
  preview: WebPreviewPayload;
  validation: ValidationResult;
  error: string | undefined;
}

export type ProgressEventType =
  | "node_started"
  | "node_complete"
  | "validation_started"
  | "retry_started"
  | "render_started"
  | "done"
  | "error";

export interface ProgressEvent {
  type: ProgressEventType;
  node: string;
  message: string | undefined;
  timestamp: string;
}

export type GenerationStage =
  | "idle"
  | "planning"
  | "generating"
  | "validating"
  | "rendering"
  | "done"
  | "error";
