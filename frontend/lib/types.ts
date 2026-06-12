// Mirrors backend/types.py. When changing fields in either file, update both in the same commit.

export type LengthPreset = "short" | "standard" | "long";

export interface TopicDomains {
  model_passage: string;
  assessment_passage: string;
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

export const PROMPT_LAB_SECTION_KEYS = [
  "intro",
  "learning_targets",
  "warmup",
  "vocabulary",
  "core_explainer",
  "subconcept",
  "strategy_list",
  "deep_dive",
  "model_passage",
  "check_in",
  "key_points",
  "assessment_passage",
  "assessment_questions",
  "step_up",
  "self_assessment",
  "answer_key",
] as const;

export type PromptLabSectionKey = (typeof PROMPT_LAB_SECTION_KEYS)[number];

export const PROMPT_LAB_SAMPLE_CASE_IDS = [
  "english_grade6_ph",
  "math_grade4_vn",
  "nursing_grade12_ph",
  "science_grade8_ph",
  "social_studies_grade7_ph",
] as const;

export type PromptLabSampleCaseId = (typeof PROMPT_LAB_SAMPLE_CASE_IDS)[number];

export interface PromptLabPromptOverrides {
  system_prompt_append?: string;
  section_overrides: Partial<Record<PromptLabSectionKey, string>>;
}

export interface PromptLabGenerateRequest {
  base_request: GenerateRequest;
  prompt_overrides: PromptLabPromptOverrides;
  sample_case_id?: PromptLabSampleCaseId;
  reviewer_label?: string;
}

export interface PromptLabSampleInput {
  id: PromptLabSampleCaseId;
  label: string;
  description: string;
  request: GenerateRequest;
}

export interface PromptLabSamplePickerProps {
  samples: PromptLabSampleInput[];
  selectedSampleId: string;
  onSelectedSampleIdChange: (sampleId: string) => void;
  onApplySample: () => void;
  isLoading: boolean;
  errorMessage?: string;
}

export interface PromptLabEditorProps {
  baseRequestJson: string;
  onBaseRequestJsonChange: (value: string) => void;
  systemPromptAppend: string;
  onSystemPromptAppendChange: (value: string) => void;
  sectionOverrides: Record<PromptLabSectionKey, string>;
  onSectionOverrideChange: (
    section: PromptLabSectionKey,
    value: string,
  ) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  errorMessage?: string;
}

export interface InputFormProps {
  onSubmit: (request: GenerateRequest) => void;
  isLoading: boolean;
}

export interface ProgressTrackerProps {
  stage: GenerationStage;
  events: ProgressEvent[];
  elapsedSeconds: number;
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
  deep_dive_dimensions: string[];
}

export interface CheckInQuestion {
  number: number;
  question: string;
  evidence_hint: string;
  expected_response_type: string;
}

export interface CheckInSectionContent {
  title: string;
  passage_title: string;
  questions: CheckInQuestion[];
}

export type AssessmentQuestionItem = CheckInQuestion;

export interface AssessmentQuestionsSectionContent {
  title: string;
  passage_title: string;
  questions: AssessmentQuestionItem[];
}

export interface AnswerKeyItem {
  question_number: number;
  question: string;
  possible_answer: string;
  evidence_quote: string;
}

export interface PreviewSection {
  section_id: string;
  section_type: string;
  title: string;
  icon_key?: string;
  content: Record<string, unknown>;
}

export interface WebPreviewPayload {
  sections: PreviewSection[];
}

export interface PreviewSectionProps {
  section: PreviewSection;
  validation: ValidationResult;
}

export interface WebPreviewProps {
  preview: WebPreviewPayload;
  validation: ValidationResult;
}

export interface DownloadButtonProps {
  pdfBase64: string;
  filename: string;
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
